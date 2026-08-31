"""test_trade_persistence.py

Week 4 — Resiliency tests for the SQLite trade persistence layer.

Coverage
--------
* Successful single-trade persistence (TradeLedger.save_trade)
* Successful multi-trade persistence (TradeLedger.save_trades)
* Database read-back via get_recent_trades and count
* save_trade returns False when the database is unavailable
* save_trades returns 0 when the database is unavailable
* Matching engine continues processing after persistence failure
* TradePersistenceWorker: async background persistence
* TradePersistenceWorker: submit_many persists all trades
* TradePersistenceWorker: invalid records are silently dropped (no crash)
* Pipeline: run_matching_pipeline with persist=True writes to DB
* Pipeline: run_matching_pipeline with persist=False still returns trades
"""
import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.types import Order, OrderSide
from database.trade_ledger import TradeLedger
from database.trade_persistence_worker import TradePersistenceWorker
from engine.matching_engine import MatchingEngine, Trade
from simulator.matching_pipeline import run_matching_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trade(
    buy_order_id: int = 1,
    sell_order_id: int = 2,
    price: int = 65000,
    quantity: int = 10,
) -> Trade:
    now = time.perf_counter_ns()
    return Trade(
        buy_order_id=buy_order_id,
        sell_order_id=sell_order_id,
        price=price,
        quantity=quantity,
        engine_enter_ns=now,
        engine_exit_ns=now + 1000,
        latency_ns=1000,
    )


def _make_order(order_id, side, price, quantity) -> Order:
    return Order(
        order_id=order_id,
        side=side,
        price=price,
        quantity=quantity,
        timestamp=time.perf_counter_ns(),
    )


# ---------------------------------------------------------------------------
# TradeLedger — successful persistence
# ---------------------------------------------------------------------------

class TestTradeLedgerPersistence:

    def test_save_single_trade(self, tmp_path):
        """save_trade stores a trade and count returns 1."""
        ledger = TradeLedger(tmp_path / "trades.db")
        trade = _make_trade()

        result = ledger.save_trade(trade)

        assert result is True
        assert ledger.count() == 1

    def test_save_trade_fields_are_correct(self, tmp_path):
        """Persisted fields match the original Trade object."""
        ledger = TradeLedger(tmp_path / "trades.db")
        trade = _make_trade(buy_order_id=7, sell_order_id=8, price=70000, quantity=5)

        ledger.save_trade(trade)

        rows = ledger.get_recent_trades(1)
        assert len(rows) == 1

        _, buy_id, sell_id, price, qty, *_ = rows[0]
        assert buy_id == 7
        assert sell_id == 8
        assert price == 70000
        assert qty == 5

    def test_save_multiple_trades_individually(self, tmp_path):
        """Multiple individual save_trade calls all persist."""
        ledger = TradeLedger(tmp_path / "trades.db")
        n = 5

        for i in range(n):
            ledger.save_trade(_make_trade(buy_order_id=i + 1, sell_order_id=i + 100))

        assert ledger.count() == n

    def test_save_trades_batch(self, tmp_path):
        """save_trades persists a list of trades atomically."""
        ledger = TradeLedger(tmp_path / "trades.db")
        trades = [_make_trade(buy_order_id=i, sell_order_id=i + 50) for i in range(1, 6)]

        saved = ledger.save_trades(trades)

        assert saved == 5
        assert ledger.count() == 5

    def test_save_trades_empty_list_returns_zero(self, tmp_path):
        """save_trades with an empty list is a no-op and returns 0."""
        ledger = TradeLedger(tmp_path / "trades.db")
        assert ledger.save_trades([]) == 0
        assert ledger.count() == 0

    def test_get_recent_trades_order(self, tmp_path):
        """get_recent_trades returns rows newest-first."""
        ledger = TradeLedger(tmp_path / "trades.db")

        for i in range(1, 4):
            ledger.save_trade(_make_trade(buy_order_id=i))

        rows = ledger.get_recent_trades(3)
        assert len(rows) == 3
        # trade_ids should be descending
        assert rows[0][0] > rows[1][0] > rows[2][0]

    def test_get_recent_trades_limit(self, tmp_path):
        """get_recent_trades respects the limit parameter."""
        ledger = TradeLedger(tmp_path / "trades.db")

        for i in range(1, 11):
            ledger.save_trade(_make_trade(buy_order_id=i))

        rows = ledger.get_recent_trades(3)
        assert len(rows) == 3

    def test_count_multiple_trades(self, tmp_path):
        """count returns the correct total after several inserts."""
        ledger = TradeLedger(tmp_path / "trades.db")
        trades = [_make_trade(buy_order_id=i) for i in range(1, 8)]
        ledger.save_trades(trades)
        assert ledger.count() == 7


# ---------------------------------------------------------------------------
# TradeLedger — failure handling
# ---------------------------------------------------------------------------

class TestTradeLedgerFailureHandling:

    def test_save_trade_returns_false_on_db_error(self, tmp_path):
        """save_trade returns False (not raises) when the DB write fails."""
        ledger = TradeLedger(tmp_path / "trades.db")
        trade = _make_trade()

        # Simulate a database error by patching the internal connection method.
        with patch.object(ledger, "_connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = sqlite3.Error("disk full")
            mock_connect.return_value = mock_conn

            result = ledger.save_trade(trade)

        assert result is False

    def test_save_trades_returns_zero_on_db_error(self, tmp_path):
        """save_trades returns 0 (not raises) when the DB write fails."""
        ledger = TradeLedger(tmp_path / "trades.db")
        trades = [_make_trade(buy_order_id=i) for i in range(1, 4)]

        with patch.object(ledger, "_connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.executemany.side_effect = sqlite3.Error("disk full")
            mock_connect.return_value = mock_conn

            result = ledger.save_trades(trades)

        assert result == 0

    def test_save_trade_invalid_record_type_returns_false(self, tmp_path):
        """save_trade returns False and does not crash on invalid input."""
        ledger = TradeLedger(tmp_path / "trades.db")
        result = ledger.save_trade("this is not a Trade")  # type: ignore
        assert result is False

    def test_save_trades_skips_invalid_records(self, tmp_path):
        """save_trades silently skips non-Trade items in the list."""
        ledger = TradeLedger(tmp_path / "trades.db")
        trades_with_garbage = [
            _make_trade(buy_order_id=1),
            "not a trade",          # invalid
            None,                   # invalid
            _make_trade(buy_order_id=2),
        ]
        saved = ledger.save_trades(trades_with_garbage)  # type: ignore

        # Only the two valid Trade objects should have been written.
        assert saved == 2
        assert ledger.count() == 2


# ---------------------------------------------------------------------------
# TradePersistenceWorker — async persistence
# ---------------------------------------------------------------------------

class TestTradePersistenceWorker:

    def test_worker_persists_single_trade(self, tmp_path):
        """Worker saves one trade to the DB after flush."""
        worker = TradePersistenceWorker(str(tmp_path / "w.db"))
        worker.submit(_make_trade())
        worker.flush()
        assert worker.ledger.count() == 1
        worker.stop()

    def test_worker_persists_multiple_trades(self, tmp_path):
        """Worker saves all trades submitted via submit_many."""
        worker = TradePersistenceWorker(str(tmp_path / "w.db"))
        trades = [_make_trade(buy_order_id=i) for i in range(1, 6)]
        worker.submit_many(trades)
        worker.flush()
        assert worker.ledger.count() == 5
        worker.stop()

    def test_worker_db_readback(self, tmp_path):
        """Trades persisted by the worker can be read back correctly."""
        worker = TradePersistenceWorker(str(tmp_path / "w.db"))
        trade = _make_trade(buy_order_id=42, sell_order_id=99, price=70000, quantity=3)
        worker.submit(trade)
        worker.flush()

        rows = worker.ledger.get_recent_trades(1)
        assert len(rows) == 1
        _, buy_id, sell_id, price, qty, *_ = rows[0]
        assert buy_id == 42
        assert sell_id == 99
        assert price == 70000
        assert qty == 3

        worker.stop()

    def test_worker_invalid_record_is_dropped_safely(self, tmp_path):
        """submit with a non-Trade value is silently ignored; no crash."""
        worker = TradePersistenceWorker(str(tmp_path / "w.db"))
        worker.submit("not a trade")  # type: ignore
        worker.submit(None)           # type: ignore
        time.sleep(0.1)              # allow the worker thread to cycle
        assert worker.ledger.count() == 0
        worker.stop()

    def test_worker_continues_after_persistence_failure(self, tmp_path):
        """The worker thread stays alive and processes later trades even when
        an earlier save_trade call fails (e.g. transient DB error)."""
        worker = TradePersistenceWorker(str(tmp_path / "w.db"))

        fail_count = 0
        original_save = worker.ledger.save_trade

        call_count = {"n": 0}

        def flaky_save(trade):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Simulate first call failing.
                return False
            return original_save(trade)

        worker.ledger.save_trade = flaky_save

        # Submit 3 trades — first will fail, next two should succeed.
        for i in range(1, 4):
            worker.submit(_make_trade(buy_order_id=i))

        worker.flush()
        # Only 2 of the 3 were actually saved (first was dropped).
        assert worker.ledger.count() == 2
        worker.stop()

    def test_worker_pending_reflects_queue_size(self, tmp_path):
        """pending() returns a non-negative integer."""
        worker = TradePersistenceWorker(str(tmp_path / "w.db"))
        pending_before = worker.pending()
        assert isinstance(pending_before, int)
        assert pending_before >= 0
        worker.stop()

    def test_worker_stop_drains_queue(self, tmp_path):
        """stop() flushes remaining trades before returning."""
        worker = TradePersistenceWorker(str(tmp_path / "w.db"))
        trades = [_make_trade(buy_order_id=i) for i in range(1, 11)]
        worker.submit_many(trades)
        worker.stop()
        assert worker.ledger.count() == 10


# ---------------------------------------------------------------------------
# Matching engine — remains responsive under persistence failures
# ---------------------------------------------------------------------------

class TestMatchingEngineResiliency:

    def test_engine_continues_matching_when_db_fails(self, tmp_path):
        """Matching engine produces correct trades regardless of DB state.

        This verifies the core resiliency requirement: a broken database
        must not block or crash the matching engine.
        """
        engine = MatchingEngine()
        worker = TradePersistenceWorker(str(tmp_path / "broken.db"))

        # Make every save attempt fail silently.
        worker.ledger.save_trade = lambda _: False

        all_trades = []

        orders = [
            _make_order(1, OrderSide.BUY, 65000, 10),
            _make_order(2, OrderSide.SELL, 65000, 5),
            _make_order(3, OrderSide.SELL, 65000, 5),
            _make_order(4, OrderSide.BUY, 65000, 3),
            _make_order(5, OrderSide.SELL, 65000, 3),
        ]

        for order in orders:
            new_trades = engine.process_order(order)
            all_trades.extend(new_trades)
            worker.submit_many(new_trades)

        worker.stop()

        # Engine should have matched correctly.
        assert len(all_trades) >= 1
        total_qty = sum(t.quantity for t in all_trades)
        assert total_qty > 0

    def test_engine_produces_trades_independently_of_persistence(self, tmp_path):
        """Trade objects returned by process_order are correct even when
        persistence is completely unavailable."""
        engine = MatchingEngine()

        buy = _make_order(1, OrderSide.BUY, 65000, 10)
        sell = _make_order(2, OrderSide.SELL, 65000, 10)

        engine.process_order(buy)
        trades = engine.process_order(sell)

        assert len(trades) == 1
        assert trades[0].buy_order_id == 1
        assert trades[0].sell_order_id == 2
        assert trades[0].quantity == 10


# ---------------------------------------------------------------------------
# Integration — run_matching_pipeline with persistence
# ---------------------------------------------------------------------------

class TestMatchingPipelineWithPersistence:

    def test_pipeline_with_persistence_writes_to_db(self, tmp_path):
        """run_matching_pipeline with persist=True persists trades to DB."""
        db_path = str(tmp_path / "pipeline.db")
        trades = run_matching_pipeline(
            order_count=200,
            database_path=db_path,
            persist=True,
        )

        assert isinstance(trades, list)

        # Confirm that something was persisted.
        ledger = TradeLedger(db_path)
        persisted_count = ledger.count()
        assert persisted_count == len(trades)

    def test_pipeline_without_persistence_still_returns_trades(self, tmp_path):
        """run_matching_pipeline with persist=False still works correctly."""
        trades = run_matching_pipeline(
            order_count=100,
            persist=False,
        )
        assert isinstance(trades, list)

    def test_pipeline_trade_objects_are_valid(self, tmp_path):
        """All Trade objects returned by the pipeline have positive fields."""
        trades = run_matching_pipeline(order_count=200, persist=False)
        for trade in trades:
            assert trade.buy_order_id > 0
            assert trade.sell_order_id > 0
            assert trade.price > 0
            assert trade.quantity > 0
