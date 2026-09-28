from decimal import Decimal

import pytest

from stock_engine.portfolio import PaperBroker, money


def test_buy_sell_realized_unrealized_and_cash_conservation():
    broker = PaperBroker(10000)
    broker.seed_liquidity("AAA", 100, spread=0)
    buy = broker.place_market_order("AAA", "BUY", 10)
    assert buy.filled == 10
    assert broker.cash == Decimal("8999.90")
    assert broker.positions["AAA"].average_cost == Decimal("100.01")
    broker.seed_liquidity("AAA", 110, spread=0)
    broker.place_market_order("AAA", "SELL", 4)
    result = broker.valuation({"AAA": 110})
    assert result["realized_pnl"] == Decimal("39.92")
    assert result["unrealized_pnl"] == Decimal("59.94")
    assert result["total_pnl"] == Decimal("99.86")
    assert result["total_pnl"] == result["realized_pnl"] + result["unrealized_pnl"]
    assert result["equity"] == result["cash"] + result["market_value"]
    broker.place_market_order("AAA", "SELL", 6)
    assert broker.valuation({})["holdings"] == []
    assert broker.realized_pnl == Decimal("99.80")
    assert broker.positions["AAA"].cost == 0


def test_multiple_purchase_costs_and_average_cost_sale():
    broker = PaperBroker(10000)
    broker.seed_liquidity("AAA", 100, spread=0)
    broker.place_market_order("AAA", "BUY", 10)
    broker.seed_liquidity("AAA", 120, spread=0)
    broker.place_market_order("AAA", "BUY", 10)
    assert broker.positions["AAA"].average_cost == Decimal("110.01")
    broker.seed_liquidity("AAA", 130, spread=0)
    broker.place_market_order("AAA", "SELL", 5)
    assert broker.realized_pnl == Decimal("99.90")
    assert broker.positions["AAA"].quantity == 15
    assert broker.positions["AAA"].cost == Decimal("1650.15")


def test_partial_market_fill_expires_and_only_filled_shares_are_booked():
    broker = PaperBroker(10000)
    broker.seed_liquidity("AAA", 100, shares=2, spread=0)
    result = broker.place_market_order("AAA", "BUY", 10)
    assert result.filled == 6 and result.remaining == 4 and not result.resting
    assert broker.positions["AAA"].quantity == 6
    assert broker.cash == Decimal("9399.94")
    assert len(broker.fills) == 3
    assert broker.exchange.engine.get_order(result.order_id) is None


def test_rejections_keep_balances_positions_and_journal_unchanged():
    broker = PaperBroker(100)
    broker.seed_liquidity("AAA", 100)
    before = broker.to_dict()
    for args in [("AAA", "BUY", 2), ("AAA", "SELL", 1), ("AAA", "BUY", 0), ("BBB", "BUY", 1)]:
        with pytest.raises(ValueError):
            broker.place_market_order(*args)
        assert broker.cash == 100
        assert broker.positions == {}
        assert broker.to_dict() == before


def test_paper_account_replays_after_restart():
    broker = PaperBroker(10000)
    broker.seed_liquidity("AAA", 100)
    broker.place_market_order("AAA", "BUY", 12)
    broker.seed_liquidity("AAA", 103)
    broker.place_market_order("AAA", "SELL", 5)
    broker.record_equity({"AAA": 103})
    restored = PaperBroker.from_dict(broker.to_dict())
    assert restored.valuation({"AAA": 104}) == broker.valuation({"AAA": 104})
    assert restored.to_dict() == broker.to_dict()
    assert restored.exchange.engine.order_book("AAA") == broker.exchange.engine.order_book("AAA")


@pytest.mark.parametrize("value", [0, -1, "NaN", "Infinity", "0.001", "no"])
def test_invalid_cash_amounts_are_rejected(value):
    with pytest.raises(ValueError):
        money(value)
