from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import random

import pytest

from stock_engine import MatchingEngine
from stock_engine.structures import AVLTree, FenwickTree


def test_example_matches_at_resting_price_and_partially_fills():
    engine = MatchingEngine()
    engine.place_order("S1", "ACME", "SELL", 150, "105.00")
    engine.place_order("S2", "ACME", "SELL", 100, "106.00")

    result = engine.place_order("B1", "ACME", "BUY", 100, "106.00")

    assert result.filled == 100
    assert result.remaining == 0
    assert [(trade.price, trade.quantity) for trade in result.trades] == [(Decimal("105.00"), 100)]
    assert engine.order_book("ACME")["asks"] == [
        {"price": "105.00", "quantity": 50, "orders": 1},
        {"price": "106.00", "quantity": 100, "orders": 1},
    ]


def test_price_time_priority_and_market_remainder():
    engine = MatchingEngine()
    engine.place_order("S1", "XYZ", "SELL", 50, "100.00")
    engine.place_order("S2", "XYZ", "SELL", 70, "100.00")
    engine.place_order("S3", "XYZ", "SELL", 30, "101.00")

    result = engine.place_order("B1", "XYZ", "BUY", 200)

    assert [(trade.sell_order_id, trade.quantity) for trade in result.trades] == [
        ("S1", 50), ("S2", 70), ("S3", 30)
    ]
    assert result.remaining == 50 and not result.resting
    assert engine.order_book("XYZ")["asks"] == []
    assert engine.get_order("B1") is None


def test_cancel_modify_and_multiple_symbols():
    engine = MatchingEngine()
    engine.place_order("B1", "AAA", "BUY", 10, "100.00")
    engine.place_order("B2", "AAA", "BUY", 10, "100.00")
    engine.place_order("X1", "BBB", "SELL", 5, "90.00")
    assert engine.cancel_order("B1")
    assert not engine.cancel_order("B1")
    engine.place_order("B3", "AAA", "BUY", 10, "100.00")
    engine.modify_order("B2", 20, "100.00")
    result = engine.place_order("S1", "AAA", "SELL", 15, "100.00")
    assert [(trade.buy_order_id, trade.quantity) for trade in result.trades] == [("B3", 10), ("B2", 5)]
    assert engine.get_order("B2")["remaining"] == 15
    assert engine.order_book("BBB")["asks"][0]["quantity"] == 5


def test_statistics_volume_ranges_and_trade_lookup():
    engine = MatchingEngine()
    engine.place_order("S1", "AAA", "SELL", 10, "10.00")
    engine.place_order("B1", "AAA", "BUY", 10, "10.00")
    engine.place_order("S2", "AAA", "SELL", 20, "12.00")
    engine.place_order("B2", "AAA", "BUY", 20, "12.00")
    engine.place_order("S3", "BBB", "SELL", 5, "20.00")
    engine.place_order("B3", "BBB", "BUY", 5, "20.00")

    assert engine.traded_volume("AAA", 1, 2) == 20
    assert engine.symbol_stats("AAA") == {
        "symbol": "AAA", "trades": 2, "volume": 30,
        "open": "10.00", "high": "12.00", "low": "10.00", "last": "12.00", "vwap": "11.33",
    }
    assert engine.trade_by_id(2).sell_order_id == "S2"
    assert engine.trade_by_id(999) is None
    assert engine.top_traded_stocks() == [
        {"symbol": "AAA", "volume": 30}, {"symbol": "BBB", "volume": 5}
    ]


def test_invalid_input_does_not_consume_id_or_modify_existing_order():
    engine = MatchingEngine()
    with pytest.raises(ValueError):
        engine.place_order("A", "AAA", "BUY", 0, "10.00")
    engine.place_order("A", "AAA", "BUY", 10, "10.00")
    with pytest.raises(ValueError):
        engine.place_order("A", "AAA", "BUY", 10, "10.00")
    with pytest.raises(ValueError):
        engine.modify_order("A", 5, "NaN")
    assert engine.get_order("A")["remaining"] == 10
    with pytest.raises(ValueError):
        engine.place_order("B", "AAA", "BUY", 10, "10.001")


def test_avl_tree_deletions_and_ordering():
    rng = random.Random(7)
    keys = list(range(300))
    rng.shuffle(keys)
    tree = AVLTree[int]()
    for key in keys:
        tree.insert(Decimal(key), key)
    assert [value for _, value in tree.items()] == list(range(300))
    rng.shuffle(keys)
    for key in keys[:250]:
        tree.delete(Decimal(key))
    assert [value for _, value in tree.items()] == sorted(keys[250:])
    assert [value for _, value in tree.items(descending=True)] == sorted(keys[250:], reverse=True)


def test_fenwick_growth_and_ranges():
    rng = random.Random(11)
    values = [rng.randrange(100) for _ in range(150)]
    tree = FenwickTree()
    for value in values:
        tree.append(value)
    for start in range(0, 150, 7):
        for end in range(start, 151, 13):
            assert tree.range_sum(start, end) == sum(values[start:end])


def test_no_cross_when_limit_prices_do_not_overlap():
    engine = MatchingEngine()
    engine.place_order("S", "AAA", "SELL", 7, "101.00")
    result = engine.place_order("B", "AAA", "BUY", 10, "100.00")
    assert result.filled == 0 and result.resting
    assert engine.order_book("AAA")["bids"][0]["quantity"] == 10
    assert engine.order_book("AAA")["asks"][0]["quantity"] == 7


def test_randomized_matching_agrees_with_simple_reference_book():
    """Compare every trade and depth snapshot against an independent list model."""
    rng = random.Random(123)
    engine = MatchingEngine()
    resting = []

    for index in range(500):
        symbol = rng.choice(["AAA", "BBB", "CCC"])
        side = rng.choice(["BUY", "SELL"])
        quantity = rng.randrange(1, 30)
        price = None if rng.randrange(8) == 0 else Decimal(rng.randrange(95, 106))
        order_id = f"R{index}"
        remaining = quantity
        expected = []

        while remaining:
            candidates = [
                order for order in resting
                if order["symbol"] == symbol and order["side"] != side
                and (price is None or (order["price"] <= price if side == "BUY" else order["price"] >= price))
            ]
            if not candidates:
                break
            maker = min(candidates, key=lambda order: (
                order["price"] if side == "BUY" else -order["price"], order["sequence"]
            ))
            shares = min(remaining, maker["remaining"])
            maker["remaining"] -= shares
            remaining -= shares
            expected.append((maker["price"], shares, maker["id"]))
            if maker["remaining"] == 0:
                resting.remove(maker)

        if remaining and price is not None:
            resting.append({"id": order_id, "symbol": symbol, "side": side, "price": price, "remaining": remaining, "sequence": index})

        result = engine.place_order(order_id, symbol, side, quantity, price)
        actual = [(trade.price, trade.quantity, trade.sell_order_id if side == "BUY" else trade.buy_order_id) for trade in result.trades]
        assert actual == expected
        assert result.remaining == remaining

        for check_symbol in ["AAA", "BBB", "CCC"]:
            book = engine.order_book(check_symbol)
            for check_side, label, reverse in [("BUY", "bids", True), ("SELL", "asks", False)]:
                levels = {}
                for order in resting:
                    if order["symbol"] == check_symbol and order["side"] == check_side:
                        levels.setdefault(order["price"], []).append(order)
                expected_depth = [
                    {"price": str(level_price), "quantity": sum(order["remaining"] for order in orders), "orders": len(orders)}
                    for level_price, orders in sorted(levels.items(), reverse=reverse)
                ]
                assert book[label] == expected_depth[:10]


def test_concurrent_submissions_conserve_shares():
    engine = MatchingEngine()
    orders = [
        (f"C{index}", "AAA", "BUY" if index % 2 else "SELL", 10, "100.00")
        for index in range(200)
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda order: engine.place_order(*order), orders))
    book = engine.order_book("AAA", depth=200)
    open_volume = sum(level["quantity"] for level in book["bids"] + book["asks"])
    assert 2 * engine.traded_volume("AAA") + open_volume == 2000
    assert not (book["bids"] and book["asks"])
