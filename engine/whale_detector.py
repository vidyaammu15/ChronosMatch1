"""engine/whale_detector.py

Whale-event detection for the ChronosMatch matching engine.

A "Whale event" is a single order that clears **two or more distinct
price levels** in one matching pass.  This is detected purely from the
list of Trade objects returned by MatchingEngine.process_order — no
fake/random logic involved.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from engine.matching_engine import Trade


# Minimum number of distinct price levels that must be cleared for an
# event to be classified as a Whale event.
WHALE_MIN_LEVELS: int = 2


@dataclass
class WhaleEvent:
    """Immutable snapshot of a detected Whale matching event."""

    order_id: int
    side: str                       # "BUY" or "SELL"
    total_quantity: int             # Quantity of the incoming whale order
    levels_cleared: int             # Number of distinct prices cleared
    prices_cleared: List[int]       # Sorted list of cleared prices
    total_matched_qty: int          # Total quantity matched across all trades
    trade_count: int                # Number of individual trades generated
    timestamp_ns: int               # engine_exit_ns of the last trade

    def to_dict(self) -> dict:
        """Serialise to a JSON-safe dict for the REST API."""
        return {
            "order_id": self.order_id,
            "side": self.side,
            "total_quantity": self.total_quantity,
            "levels_cleared": self.levels_cleared,
            "prices_cleared": self.prices_cleared,
            "total_matched_qty": self.total_matched_qty,
            "trade_count": self.trade_count,
            "timestamp_ns": self.timestamp_ns,
        }


def detect_whale(
    order_id: int,
    side: str,
    order_quantity: int,
    trades: List[Trade],
    min_levels: int = WHALE_MIN_LEVELS,
) -> Optional[WhaleEvent]:
    """Return a WhaleEvent if *trades* cleared multiple price levels.

    Parameters
    ----------
    order_id:
        ID of the incoming order that produced *trades*.
    side:
        "BUY" or "SELL".
    order_quantity:
        Quantity of the incoming order.
    trades:
        Trade objects produced by MatchingEngine.process_order for that order.
    min_levels:
        Minimum number of distinct price levels that must be cleared
        (default 2).  Must be >= 1.

    Returns
    -------
    WhaleEvent or None
        WhaleEvent if the threshold is met, None otherwise.
    """
    if not trades:
        return None

    prices = sorted({t.price for t in trades})
    levels_cleared = len(prices)

    if levels_cleared < min_levels:
        return None

    total_matched = sum(t.quantity for t in trades)
    last_trade = max(trades, key=lambda t: t.engine_exit_ns)

    return WhaleEvent(
        order_id=order_id,
        side=side,
        total_quantity=order_quantity,
        levels_cleared=levels_cleared,
        prices_cleared=prices,
        total_matched_qty=total_matched,
        trade_count=len(trades),
        timestamp_ns=last_trade.engine_exit_ns,
    )
