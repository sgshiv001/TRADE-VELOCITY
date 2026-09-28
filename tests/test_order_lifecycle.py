"""Deletion, replacement, and stale-price regression tests for the full engine."""

from decimal import Decimal
import random

import pytest

from stock_engine import MatchingEngine


@pytest.mark.parametrize("side,opposite,anchor", [("BUY", "SELL", "110.00"), ("SELL", "BUY", "90.00")])
def test_cancellation_churn_compacts_heap_and_price_recreation_is_safe(side, opposite, anchor):
    engine = MatchingEngine()
    engine.place_order("anchor", "AAA", side, 1, anchor)
    for index in range(250):
        order_id = f"churn{index}"
        engine.place_order(order_id, "AAA", side, 2, "100.00")
        assert engine.cancel_order(order_id)
    book_side = engine._books["AAA"][0 if side == "BUY" else 1]
    assert len(book_side.heap) <= 2 * len(book_side.active_levels) + 64

    engine.place_order("recreated", "AAA", side, 7, "100.00")
    result = engine.place_order("market", "AAA", opposite, 5)
    maker_ids = [trade.buy_order_id if side == "BUY" else trade.sell_order_id for trade in result.trades]
    assert maker_ids == ["anchor", "recreated"]
    assert engine.get_order("recreated")["remaining"] == 3
    assert engine.traded_volume("AAA") == 5


def test_mixed_order_lifecycle_matches_independent_reference():
    """Compare placement, cancellation, and replacement with a sorted list model."""
    rng = random.Random(811)
    engine = MatchingEngine()
    resting = []
    sequence = 0
    expected_history = []

    def place(order_id, symbol, side, quantity, price):
        nonlocal sequence
        sequence += 1
        remaining = quantity
        expected_trades = []
        while remaining:
            candidates = [order for order in resting if order["symbol"] == symbol and order["side"] != side
                          and (price is None or (order["price"] <= price if side == "BUY" else order["price"] >= price))]
            if not candidates:
                break
            maker = min(candidates, key=lambda order: (order["price"] if side == "BUY" else -order["price"], order["sequence"]))
            shares = min(remaining, maker["remaining"])
            buy_id, sell_id = (order_id, maker["order_id"]) if side == "BUY" else (maker["order_id"], order_id)
            expected_trades.append((symbol, maker["price"], shares, buy_id, sell_id))
            maker["remaining"] -= shares
            remaining -= shares
            if not maker["remaining"]:
                resting.remove(maker)
        if remaining and price is not None:
            resting.append({"order_id": order_id, "symbol": symbol, "side": side, "quantity": quantity,
                            "remaining": remaining, "price": price, "sequence": sequence})
        expected_history.extend(expected_trades)
        return remaining, expected_trades

    for index in range(1200):
        action = rng.randrange(5)
        if resting and action == 0:
            old = rng.choice(resting)
            assert engine.cancel_order(old["order_id"])
            assert not engine.cancel_order(old["order_id"])
            resting.remove(old)
        else:
            quantity = rng.randrange(1, 40)
            price = Decimal(rng.randrange(95, 106))
            if resting and action == 1:
                old = rng.choice(resting)
                resting.remove(old)
                order_id, symbol, side = old["order_id"], old["symbol"], old["side"]
                result = engine.modify_order(order_id, quantity, price)
            else:
                order_id = f"O{index}"
                symbol = rng.choice(["AAA", "BBB", "CCC"])
                side = rng.choice(["BUY", "SELL"])
                price = None if rng.randrange(10) == 0 else price
                result = engine.place_order(order_id, symbol, side, quantity, price)
            remaining, expected = place(order_id, symbol, side, quantity, price)
            assert result.remaining == remaining
            assert result.filled == quantity - remaining
            assert result.resting == (remaining > 0 and price is not None)
            assert [(trade.symbol, trade.price, trade.quantity, trade.buy_order_id, trade.sell_order_id)
                    for trade in result.trades] == expected

        assert engine.active_orders() == [dict(order, price=str(order["price"]))
                                          for order in sorted(resting, key=lambda order: order["sequence"])]
        for symbol in ["AAA", "BBB", "CCC"]:
            book = engine.order_book(symbol, depth=100)
            for side, label, descending in [("BUY", "bids", True), ("SELL", "asks", False)]:
                prices = sorted({order["price"] for order in resting if order["symbol"] == symbol and order["side"] == side}, reverse=descending)
                expected_depth = []
                for price in prices:
                    orders = [order for order in resting if order["symbol"] == symbol and order["side"] == side and order["price"] == price]
                    expected_depth.append({"price": str(price), "quantity": sum(order["remaining"] for order in orders), "orders": len(orders)})
                assert book[label] == expected_depth
            assert engine.traded_volume(symbol) == sum(trade[2] for trade in expected_history if trade[0] == symbol)

    assert [(trade.symbol, trade.price, trade.quantity, trade.buy_order_id, trade.sell_order_id)
            for trade in engine.trades()] == expected_history
