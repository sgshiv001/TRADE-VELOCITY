"""Cash and inventory rules for the funded paper venue."""

from decimal import Decimal
import re
from uuid import uuid4

from .account_summary import account_portfolio
from .models import Side
from .session import ExchangeSession

VIRTUAL_MAKER = "tradevelocity-virtual-maker"


def validate_limit(exchange: ExchangeSession, owner: str, symbol: str, side: str, quantity: int,
                   price: str, credits: list[dict], replacing: dict | None = None):
    if not re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,2})?", price):
        raise ValueError("Enter a limit price with up to ten whole digits and two decimal places")
    symbol, side, price = exchange.engine._validate(symbol, side, quantity, price)
    if price is None:
        raise ValueError("Enter a limit price")
    active = exchange.engine.active_orders(symbol)
    mine = [order for order in active if exchange.owners.get(order["order_id"]) == owner
            and (not replacing or order["order_id"] != replacing["order_id"])]
    for order in mine:
        resting_price = Decimal(order["price"])
        crosses = price >= resting_price if side == Side.BUY else price <= resting_price
        if order["side"] != side.value and crosses:
            raise ValueError("Cancel the crossing order you already own before placing this order")
    portfolio = account_portfolio(exchange, owner, {}, credits)
    if side == Side.BUY:
        available = Decimal(portfolio["available_cash"])
        if replacing:
            available += Decimal(replacing["price"]) * replacing["remaining"]
        if price * quantity > available:
            raise ValueError("Insufficient available virtual cash after open orders")
    else:
        owned = next((row["quantity"] for row in portfolio["holdings"] if row["symbol"] == symbol), 0)
        reserved = sum(order["remaining"] for order in mine if order["side"] == "SELL")
        if quantity > owned - reserved:
            raise ValueError("Insufficient shares after open sell orders")
    return symbol, side, price


def refresh_virtual_depth(exchange: ExchangeSession, symbol: str, price: Decimal):
    """Keep maker orders visible and leave all user orders under user control."""
    if price < Decimal("0.02"):
        raise ValueError("The reference price is too small for paper depth")
    gap = max(Decimal("0.01"), (price * Decimal("0.0015")).quantize(Decimal("0.01")))
    for order in exchange.engine.active_orders(symbol):
        if exchange.owners.get(order["order_id"]) == VIRTUAL_MAKER:
            exchange.cancel_order(order["order_id"])
    for side, level in (("BUY", price - gap), ("SELL", price + gap)):
        exchange.place_order(f"SIM-{uuid4()}", symbol, side, 100, str(level), owner=VIRTUAL_MAKER)
