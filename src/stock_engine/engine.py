"""Deterministic, price-time-priority matching for multiple symbols."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from threading import RLock

from .models import Order, OrderResult, Side, Trade
from .structures import AVLTree, BinaryHeap, FenwickTree, HashTable, LinkedQueue, QueueNode

CURRENT_TIME = object()


@dataclass(slots=True)
class PriceLevel:
    price: Decimal
    token: int
    orders: LinkedQueue[Order]
    quantity: int = 0


@dataclass(slots=True)
class SymbolTotals:
    trades: int = 0
    volume: int = 0
    notional: Decimal = Decimal(0)
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    last: Decimal | None = None

    def record(self, price: Decimal, quantity: int) -> None:
        self.trades += 1
        self.volume += quantity
        self.notional += price * quantity
        if self.open is None:
            self.open = price
            self.high = price
            self.low = price
        else:
            assert self.high is not None and self.low is not None
            self.high = max(self.high, price)
            self.low = min(self.low, price)
        self.last = price


class BookSide:
    def __init__(self, is_buy: bool):
        self.is_buy = is_buy
        self.levels: AVLTree[PriceLevel] = AVLTree()
        self.heap: BinaryHeap[tuple[Decimal, int]] = BinaryHeap(
            lambda a, b: a[0] > b[0] if is_buy else a[0] < b[0]
        )
        self.active_levels: HashTable[Decimal, PriceLevel] = HashTable()
        self.next_token = 0

    def best(self) -> PriceLevel | None:
        while self.heap:
            price, token = self.heap.peek()
            level = self.active_levels.get(price)
            if level is None or level.token != token:
                self.heap.pop()
                continue
            return level
        return None

    def add(self, order: Order) -> QueueNode[Order]:
        assert order.price is not None
        level = self.active_levels.get(order.price)
        if level is None:
            self.next_token += 1
            level = PriceLevel(order.price, self.next_token, LinkedQueue())
            self.levels.insert(order.price, level)
            self.active_levels[order.price] = level
            self.heap.push((order.price, level.token))
        node = level.orders.append(order)
        level.quantity += order.remaining
        return node

    def remove(self, order: Order, node: QueueNode[Order]) -> None:
        assert order.price is not None
        level = self.active_levels.get(order.price)
        assert level is not None
        level.quantity -= order.remaining
        level.orders.remove(node)
        if level.orders.length == 0:
            self.levels.delete(level.price)
            del self.active_levels[level.price]
            # Old heap entries are discarded lazily. Compact occasionally so
            # repeated cancellation at non-best prices cannot grow memory forever.
            if len(self.heap) > 2 * len(self.active_levels) + 64:
                self.heap = BinaryHeap(
                    lambda a, b: a[0] > b[0] if self.is_buy else a[0] < b[0],
                    ((price, level.token) for price, level in self.active_levels.items()),
                )

    def depth(self, limit: int) -> list[dict]:
        rows = []
        for price, level in self.levels.items(descending=self.is_buy):
            if len(rows) == limit:
                break
            rows.append({"price": str(price), "quantity": level.quantity, "orders": level.orders.length})
        return rows


class MatchingEngine:
    """One locked engine instance; orders execute at the resting order's price."""

    def __init__(self):
        self._books: defaultdict[str, tuple[BookSide, BookSide]] = defaultdict(lambda: (BookSide(True), BookSide(False)))
        self._active: HashTable[str, tuple[Order, QueueNode[Order]]] = HashTable()
        self._used_ids: set[str] = set()
        self._sequence = 0
        self._trades: list[Trade] = []
        self._symbol_trades: defaultdict[str, list[Trade]] = defaultdict(list)
        self._volume: defaultdict[str, FenwickTree] = defaultdict(FenwickTree)
        self._stats: defaultdict[str, SymbolTotals] = defaultdict(SymbolTotals)
        self._lock = RLock()

    @staticmethod
    def _validate(symbol: str, side: Side | str, quantity: int, price: Decimal | str | int | None):
        if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z][A-Z0-9.]{0,15}", symbol.upper()):
            raise ValueError("symbol must be 1-16 letters, digits, or dots, starting with a letter")
        try:
            parsed_side = Side(side.upper() if isinstance(side, str) else side)
        except ValueError as exc:
            raise ValueError("side must be BUY or SELL") from exc
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        if price is None:
            parsed_price = None
        else:
            try:
                parsed_price = Decimal(str(price))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("price must be a positive amount with at most two decimals") from exc
            if not parsed_price.is_finite() or parsed_price <= 0 or parsed_price.as_tuple().exponent < -2:
                raise ValueError("price must be a positive amount with at most two decimals")
        return symbol.upper(), parsed_side, parsed_price

    def place_order(
        self,
        order_id: str,
        symbol: str,
        side: Side | str,
        quantity: int,
        price: Decimal | str | int | None = None,
        *, timestamp: datetime | None | object = CURRENT_TIME,
    ) -> OrderResult:
        """A missing price makes a market order; its unfilled remainder expires."""
        with self._lock:
            if not isinstance(order_id, str) or not order_id.strip():
                raise ValueError("order_id must be a nonempty string")
            if order_id in self._used_ids:
                raise ValueError(f"order ID already used: {order_id}")
            symbol, side, price = self._validate(symbol, side, quantity, price)
            self._used_ids.add(order_id)
            return self._place_validated(order_id, symbol, side, quantity, price, timestamp)

    def _place_validated(self, order_id: str, symbol: str, side: Side, quantity: int, price: Decimal | None, timestamp=CURRENT_TIME) -> OrderResult:
        self._sequence += 1
        incoming = Order(order_id, symbol, side, quantity, quantity, price, self._sequence)
        buy_book, sell_book = self._books[symbol]
        opposite = sell_book if side == Side.BUY else buy_book
        trades: list[Trade] = []

        while incoming.remaining:
            level = opposite.best()
            if level is None or (price is not None and (
                level.price > price if side == Side.BUY else level.price < price
            )):
                break
            maker = level.orders.head.value  # type: ignore[union-attr]
            executed = min(incoming.remaining, maker.remaining)
            incoming.remaining -= executed
            maker.remaining -= executed
            level.quantity -= executed
            trade = Trade(
                len(self._trades) + 1,
                symbol,
                level.price,
                executed,
                incoming.order_id if side == Side.BUY else maker.order_id,
                maker.order_id if side == Side.BUY else incoming.order_id,
                **({"timestamp": timestamp} if timestamp is not CURRENT_TIME else {}),
            )
            self._trades.append(trade)
            self._symbol_trades[symbol].append(trade)
            self._volume[symbol].append(executed)
            self._stats[symbol].record(level.price, executed)
            trades.append(trade)
            if maker.remaining == 0:
                _, node = self._active.pop(maker.order_id)
                opposite.remove(maker, node)

        resting = incoming.remaining > 0 and price is not None
        if resting:
            own = buy_book if side == Side.BUY else sell_book
            self._active[order_id] = (incoming, own.add(incoming))
        return OrderResult(order_id, quantity - incoming.remaining, incoming.remaining, resting, tuple(trades))

    def cancel_order(self, order_id: str) -> bool:
        """Return False when the order has already filled, expired, or been canceled."""
        with self._lock:
            entry = self._active.pop(order_id, None)
            if entry is None:
                return False
            order, node = entry
            books = self._books[order.symbol]
            (books[0] if order.side == Side.BUY else books[1]).remove(order, node)
            return True

    def modify_order(self, order_id: str, quantity: int, price: Decimal | str | int, *, timestamp=CURRENT_TIME) -> OrderResult:
        """Replace a resting limit order; quantity is its new open quantity and priority resets."""
        with self._lock:
            entry = self._active.get(order_id)
            if entry is None:
                raise KeyError(order_id)
            old = entry[0]
            symbol, side, new_price = self._validate(old.symbol, old.side, quantity, price)
            if new_price is None:
                raise ValueError("a modified order must have a limit price")
            self.cancel_order(order_id)
            return self._place_validated(order_id, symbol, side, quantity, new_price, timestamp)

    def get_order(self, order_id: str) -> dict | None:
        with self._lock:
            entry = self._active.get(order_id)
            if entry is None:
                return None
            order = entry[0]
            return {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "price": str(order.price),
                "quantity": order.quantity,
                "remaining": order.remaining,
                "sequence": order.sequence,
            }

    def active_orders(self, symbol: str | None = None) -> list[dict]:
        """Return copies of open orders in arrival order."""
        with self._lock:
            selected = symbol.upper() if symbol is not None else None
            orders = sorted(
                (order for order, _ in self._active.values() if selected is None or order.symbol == selected),
                key=lambda order: order.sequence,
            )
            return [
                {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "price": str(order.price),
                    "quantity": order.quantity,
                    "remaining": order.remaining,
                    "sequence": order.sequence,
                }
                for order in orders
            ]

    def symbols(self) -> list[str]:
        with self._lock:
            return sorted(self._books)

    def order_book(self, symbol: str, depth: int = 10) -> dict:
        if depth < 0:
            raise ValueError("depth must be nonnegative")
        with self._lock:
            symbol = symbol.upper()
            books = self._books.get(symbol)
            return {
                "symbol": symbol,
                "bids": books[0].depth(depth) if books else [],
                "asks": books[1].depth(depth) if books else [],
            }

    def trades(self, symbol: str | None = None, limit: int | None = None) -> list[Trade]:
        with self._lock:
            if limit is not None and limit < 0:
                raise ValueError("limit must be nonnegative")
            source = self._trades if symbol is None else self._symbol_trades.get(symbol.upper(), [])
            return list(source[-limit:] if limit else source) if limit != 0 else []

    def trade_by_id(self, trade_id: int) -> Trade | None:
        """Binary search over the monotonically increasing global trade IDs."""
        with self._lock:
            low, high = 0, len(self._trades)
            while low < high:
                mid = (low + high) // 2
                if self._trades[mid].trade_id < trade_id:
                    low = mid + 1
                else:
                    high = mid
            return self._trades[low] if low < len(self._trades) and self._trades[low].trade_id == trade_id else None

    def traded_volume(self, symbol: str, start: int = 0, end: int | None = None) -> int:
        """Volume between zero-based symbol trade positions [start, end)."""
        with self._lock:
            index = self._volume.get(symbol.upper())
            if index is None:
                if start != 0 or end not in (None, 0):
                    raise ValueError("invalid trade range")
                return 0
            return index.range_sum(start, len(index.values) if end is None else end)

    def symbol_stats(self, symbol: str) -> dict:
        with self._lock:
            symbol = symbol.upper()
            totals = self._stats.get(symbol)
            if totals is None:
                return {"symbol": symbol, "trades": 0, "volume": 0, "open": None, "high": None, "low": None, "last": None, "vwap": None}
            return {
                "symbol": symbol,
                "trades": totals.trades,
                "volume": totals.volume,
                "open": str(totals.open),
                "high": str(totals.high),
                "low": str(totals.low),
                "last": str(totals.last),
                "vwap": str((totals.notional / totals.volume).quantize(Decimal("0.01"))),
            }

    def top_traded_stocks(self, limit: int = 5) -> list[dict]:
        """Return the most active symbols by executed share volume."""
        if limit < 0:
            raise ValueError("limit must be nonnegative")
        with self._lock:
            heap: BinaryHeap[tuple[int, str]] = BinaryHeap(
                lambda a, b: a[0] > b[0] or (a[0] == b[0] and a[1] < b[1]),
                ((totals.volume, symbol) for symbol, totals in self._stats.items()),
            )
            return [{"symbol": symbol, "volume": volume} for volume, symbol in (heap.pop() for _ in range(min(limit, len(heap))))]
