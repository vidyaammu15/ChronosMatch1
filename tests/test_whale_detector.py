"""test_whale_detector.py

Tests for the WhaleEvent detection logic (engine/whale_detector.py).

Coverage
--------
* No trades → no whale event
* Single-level match (< WHALE_MIN_LEVELS) → no whale event
* Multi-level match (>= WHALE_MIN_LEVELS) → whale event returned
* WhaleEvent fields are populated correctly
* prices_cleared is sorted ascending
* Total matched quantity is summed correctly
* Custom min_levels threshold is respected
* Normal single-price trades are never flagged as whale events
* to_dict() returns a JSON-serialisable dict with all expected keys
"""
import time

import pytest

from engine.matching_engine import Trade
from engine.whale_detector import WhaleEvent, detect_whale, WHALE_MIN_LEVELS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trade(price: int, quantity: int = 10, order_id: int = 1) -> Trade:
    now = time.perf_counter_ns()
    return Trade(
        buy_order_id=order_id,
        sell_order_id=order_id + 1000,
        price=price,
        quantity=quantity,
        engine_enter_ns=now,
        engine_exit_ns=now + 500,
        latency_ns=500,
    )


# ---------------------------------------------------------------------------
# No-event cases
# ---------------------------------------------------------------------------

class TestNoWhaleEvent:

    def test_empty_trades_returns_none(self):
        result = detect_whale(
            order_id=1, side="BUY", order_quantity=100, trades=[]
        )
        assert result is None

    def test_single_trade_single_level_returns_none(self):
        result = detect_whale(
            order_id=1,
            side="BUY",
            order_quantity=10,
            trades=[_trade(price=65000, quantity=10)],
        )
        assert result is None

    def test_two_trades_same_price_returns_none(self):
        """Two trades at the same price level → only 1 distinct level → no whale."""
        result = detect_whale(
            order_id=1,
            side="BUY",
            order_quantity=20,
            trades=[
                _trade(price=65000, quantity=10),
                _trade(price=65000, quantity=10),
            ],
        )
        assert result is None

    def test_custom_threshold_not_met(self):
        """Three distinct levels but threshold is 4 → no whale."""
        result = detect_whale(
            order_id=1,
            side="BUY",
            order_quantity=30,
            trades=[
                _trade(price=65000),
                _trade(price=65001),
                _trade(price=65002),
            ],
            min_levels=4,
        )
        assert result is None


# ---------------------------------------------------------------------------
# Whale event cases
# ---------------------------------------------------------------------------

class TestWhaleEventDetected:

    def test_two_distinct_price_levels_triggers_whale(self):
        result = detect_whale(
            order_id=42,
            side="BUY",
            order_quantity=20,
            trades=[
                _trade(price=65000, quantity=10),
                _trade(price=65001, quantity=10),
            ],
        )
        assert result is not None
        assert isinstance(result, WhaleEvent)

    def test_three_distinct_levels(self):
        result = detect_whale(
            order_id=7,
            side="SELL",
            order_quantity=30,
            trades=[
                _trade(price=64998, quantity=10),
                _trade(price=64999, quantity=10),
                _trade(price=65000, quantity=10),
            ],
        )
        assert result is not None
        assert result.levels_cleared == 3

    def test_event_fields_are_correct(self):
        trades = [
            _trade(price=65000, quantity=5),
            _trade(price=65001, quantity=8),
        ]
        result = detect_whale(
            order_id=99,
            side="BUY",
            order_quantity=50,
            trades=trades,
        )

        assert result.order_id == 99
        assert result.side == "BUY"
        assert result.total_quantity == 50
        assert result.levels_cleared == 2
        assert result.total_matched_qty == 13   # 5 + 8
        assert result.trade_count == 2

    def test_prices_cleared_is_sorted_ascending(self):
        trades = [
            _trade(price=65005),
            _trade(price=65001),
            _trade(price=65003),
        ]
        result = detect_whale(
            order_id=1, side="BUY", order_quantity=30, trades=trades
        )
        assert result.prices_cleared == [65001, 65003, 65005]

    def test_total_matched_qty_sums_all_trades(self):
        trades = [_trade(price=p, quantity=7) for p in [65000, 65001, 65002]]
        result = detect_whale(
            order_id=1, side="BUY", order_quantity=100, trades=trades
        )
        assert result.total_matched_qty == 21

    def test_custom_min_levels_met_exactly(self):
        """min_levels=3, exactly 3 distinct levels → whale event."""
        result = detect_whale(
            order_id=1,
            side="BUY",
            order_quantity=30,
            trades=[
                _trade(price=65000),
                _trade(price=65001),
                _trade(price=65002),
            ],
            min_levels=3,
        )
        assert result is not None
        assert result.levels_cleared == 3

    def test_duplicate_prices_in_trades_are_deduplicated(self):
        """Multiple trades at the same price count as one cleared level."""
        trades = [
            _trade(price=65000, quantity=5),
            _trade(price=65000, quantity=5),  # same price, different trade
            _trade(price=65001, quantity=10),
        ]
        result = detect_whale(
            order_id=1, side="BUY", order_quantity=20, trades=trades
        )
        assert result is not None
        assert result.levels_cleared == 2
        assert result.prices_cleared == [65000, 65001]

    def test_timestamp_is_max_exit_ns(self):
        """timestamp_ns should be the engine_exit_ns of the latest trade."""
        now = time.perf_counter_ns()
        t1 = Trade(1, 2, 65000, 5, now, now + 100, 100)
        t2 = Trade(1, 3, 65001, 5, now, now + 500, 500)   # latest
        result = detect_whale(order_id=1, side="BUY", order_quantity=10, trades=[t1, t2])
        assert result.timestamp_ns == now + 500


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

class TestWhaleEventSerialisaton:

    def test_to_dict_contains_all_keys(self):
        trades = [
            _trade(price=65000, quantity=10),
            _trade(price=65001, quantity=10),
        ]
        result = detect_whale(
            order_id=5, side="SELL", order_quantity=20, trades=trades
        )
        d = result.to_dict()

        expected_keys = {
            "order_id", "side", "total_quantity", "levels_cleared",
            "prices_cleared", "total_matched_qty", "trade_count", "timestamp_ns",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_values_match_fields(self):
        trades = [
            _trade(price=65000, quantity=7),
            _trade(price=65001, quantity=3),
        ]
        event = detect_whale(
            order_id=88, side="BUY", order_quantity=50, trades=trades
        )
        d = event.to_dict()

        assert d["order_id"] == 88
        assert d["side"] == "BUY"
        assert d["total_quantity"] == 50
        assert d["levels_cleared"] == 2
        assert d["prices_cleared"] == [65000, 65001]
        assert d["total_matched_qty"] == 10
        assert d["trade_count"] == 2


# ---------------------------------------------------------------------------
# Integration: actual MatchingEngine produces real whale events
# ---------------------------------------------------------------------------

class TestWhaleDetectorWithRealEngine:

    def test_real_engine_multi_level_buy_triggers_whale(self):
        """Use the real matching engine to confirm detection on genuine trades."""
        from core.types import Order, OrderSide
        from engine.matching_engine import MatchingEngine

        engine = MatchingEngine()

        # Place three resting SELL orders at different price levels
        for i, price in enumerate([65010, 65020, 65030], start=1):
            engine.process_order(
                Order(order_id=i, side=OrderSide.SELL, price=price, quantity=10,
                      timestamp=time.perf_counter_ns())
            )

        # A large BUY that sweeps all three levels
        whale = Order(
            order_id=999, side=OrderSide.BUY, price=65030, quantity=30,
            timestamp=time.perf_counter_ns()
        )
        trades = engine.process_order(whale)

        event = detect_whale(
            order_id=whale.order_id,
            side="BUY",
            order_quantity=whale.quantity,
            trades=trades,
        )

        assert event is not None
        assert event.levels_cleared == 3
        assert event.total_matched_qty == 30

    def test_real_engine_single_level_no_whale(self):
        """Single-level match should NOT trigger a whale event."""
        from core.types import Order, OrderSide
        from engine.matching_engine import MatchingEngine

        engine = MatchingEngine()
        engine.process_order(
            Order(order_id=1, side=OrderSide.SELL, price=65000, quantity=50,
                  timestamp=time.perf_counter_ns())
        )

        normal = Order(
            order_id=2, side=OrderSide.BUY, price=65000, quantity=10,
            timestamp=time.perf_counter_ns()
        )
        trades = engine.process_order(normal)

        event = detect_whale(
            order_id=normal.order_id,
            side="BUY",
            order_quantity=normal.quantity,
            trades=trades,
        )
        assert event is None
