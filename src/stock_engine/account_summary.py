"""Read models built from the authoritative paper order and fill journal."""

from dataclasses import dataclass
from decimal import Decimal

from .session import ExchangeSession

STARTING_CASH = Decimal("1000000.00")
CENT = Decimal("0.01")


def decimal_string(value: Decimal) -> str:
    return str(value.quantize(CENT))


@dataclass
class Position:
    quantity: int = 0
    cost: Decimal = Decimal(0)

    def apply(self, quantity: int, price: Decimal) -> Decimal:
        if self.quantity == 0 or self.quantity * quantity > 0:
            self.cost += price * abs(quantity)
            self.quantity += quantity
            return Decimal(0)
        previous = self.quantity
        average = self.cost / abs(previous)
        closing = min(abs(previous), abs(quantity))
        realized = (price - average) * closing * (1 if previous > 0 else -1)
        self.quantity += quantity
        if self.quantity == 0:
            self.cost = Decimal(0)
        elif previous * self.quantity < 0:
            self.cost = price * abs(self.quantity)
        else:
            self.cost -= average * closing
        return realized


def order_journal(exchange: ExchangeSession, owner: str | None) -> list[dict]:
    def visible(order_id: str) -> bool:
        return owner is None or exchange.owners.get(order_id) == owner

    active = {order["order_id"]: order for order in exchange.engine.active_orders()
              if visible(order["order_id"])}
    fills: dict[str, tuple[int, Decimal]] = {}
    for trade in exchange.engine.trades():
        for order_id in (trade.buy_order_id, trade.sell_order_id):
            if visible(order_id):
                shares, value = fills.get(order_id, (0, Decimal(0)))
                fills[order_id] = (shares + trade.quantity, value + trade.price * trade.quantity)
    orders: dict[str, dict] = {}
    for event in exchange.events:
        order_id = event["order_id"]
        if not visible(order_id):
            continue
        kind = event["type"]
        if kind == "place":
            orders[order_id] = {
                "order_id": order_id, "symbol": event["symbol"], "side": event["side"],
                "order_type": "limit" if event["price"] is not None else "market",
                "requested_quantity": event["quantity"], "requested_price": event["price"],
                "timestamp": event["timestamp"], "status": "open",
            }
        elif kind == "modify":
            orders[order_id].update(requested_quantity=event["quantity"], requested_price=event["price"])
        elif kind == "cancel":
            orders[order_id]["status"] = "cancelled"
    for order_id, row in orders.items():
        filled, value = fills.get(order_id, (0, Decimal(0)))
        remaining = active[order_id]["remaining"] if order_id in active else 0
        status = row["status"]
        if status != "cancelled":
            if remaining:
                status = "partially_filled" if filled else "open"
            elif row["order_type"] == "market" and filled < row["requested_quantity"]:
                status = "expired"
            else:
                status = "filled"
        row.update(status=status, filled_quantity=filled, remaining_quantity=remaining,
                   average_fill_price=decimal_string(value / filled) if filled else None)
    return list(reversed(orders.values()))


def account_portfolio(exchange: ExchangeSession, owner: str, market: dict,
                      credits: list[dict]) -> dict:
    cash = contributed = STARTING_CASH + sum(Decimal(credit["amount"]) for credit in credits)
    realized = Decimal(0)
    positions: dict[str, Position] = {}
    last_match = {}
    activity = []
    for trade in exchange.engine.trades():
        belongs = owner in (exchange.owners.get(trade.buy_order_id),
                            exchange.owners.get(trade.sell_order_id))
        if not belongs:
            continue
        last_match[trade.symbol] = trade.price
        # A same-account match transfers no inventory or cash.
        bought = trade.quantity if exchange.owners.get(trade.buy_order_id) == owner else 0
        sold = trade.quantity if exchange.owners.get(trade.sell_order_id) == owner else 0
        change = bought - sold
        if not change:
            continue
        cash -= change * trade.price
        position = positions.setdefault(trade.symbol, Position())
        realized += position.apply(change, trade.price)
        activity.append({"id": f"fill-{trade.trade_id}", "symbol": trade.symbol,
                         "amount": decimal_string(-change * trade.price), "timestamp": trade.timestamp,
                         "description": f"{'Bought' if change > 0 else 'Sold'} {abs(change)} shares"})
    reserved = Decimal(0)
    for order in exchange.engine.active_orders():
        if exchange.owners.get(order["order_id"]) != owner:
            continue
        if order["side"] == "BUY":
            reserved += Decimal(order["price"]) * order["remaining"]
    holdings = []
    holdings_value = Decimal(0)
    unrealized = Decimal(0)
    invested = Decimal(0)
    for symbol, position in sorted(positions.items()):
        if not position.quantity:
            continue
        reference = market.get(symbol)
        mark = Decimal(str(reference)) if reference is not None else last_match[symbol]
        direction = 1 if position.quantity > 0 else -1
        value = mark * position.quantity
        pnl = value - position.cost * direction
        holdings_value += value
        unrealized += pnl
        invested += position.cost
        holdings.append({"symbol": symbol, "quantity": position.quantity, "average_cost": decimal_string(position.cost / abs(position.quantity)),
                         "mark": decimal_string(mark), "mark_source": "daily_close" if reference is not None else "last_simulated_fill",
                         "value": decimal_string(value), "pnl": decimal_string(pnl)})
    return {"currency": "INR", "cash": decimal_string(cash),
            "available_cash": decimal_string(cash - reserved), "reserved": decimal_string(reserved),
            "contributed": decimal_string(contributed), "invested": decimal_string(invested),
            "holdings_value": decimal_string(holdings_value), "equity": decimal_string(cash + holdings_value),
            "realized": decimal_string(realized), "unrealized": decimal_string(unrealized),
            "holdings": holdings, "activity": [*reversed(activity), *reversed(credits)]}
