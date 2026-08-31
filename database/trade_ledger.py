import logging
import sqlite3
import threading
from pathlib import Path

from engine.matching_engine import Trade

logger = logging.getLogger(__name__)


class TradeLedger:
    """Persistent SQLite ledger for matched trades.

    All write methods are safe to call from the matching-engine path:
    database errors are caught, logged, and never re-raised so they
    cannot crash the engine.
    """

    def __init__(self, database_path="trades.db"):
        self.database_path = Path(database_path)
        self._lock = threading.Lock()
        self._initialize()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self):
        return sqlite3.connect(
            self.database_path,
            check_same_thread=False,
        )

    def _initialize(self):
        """Create the trades table if it does not already exist."""
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    buy_order_id  INTEGER NOT NULL,
                    sell_order_id INTEGER NOT NULL,
                    price         INTEGER NOT NULL,
                    quantity      INTEGER NOT NULL,
                    engine_enter_ns INTEGER NOT NULL,
                    engine_exit_ns  INTEGER NOT NULL,
                    latency_ns      INTEGER NOT NULL,
                    created_at_ns   INTEGER NOT NULL
                )
                """
            )
            connection.commit()
        except sqlite3.Error as exc:
            logger.error("TradeLedger: failed to initialise schema: %s", exc)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def save_trade(self, trade: Trade) -> bool:
        """Persist one matched trade.

        Returns True on success, False if persistence failed.
        Database errors are logged and never re-raised.
        """
        if not isinstance(trade, Trade):
            logger.warning(
                "TradeLedger.save_trade: received invalid record type %s; skipping",
                type(trade).__name__,
            )
            return False

        with self._lock:
            connection = self._connect()
            try:
                connection.execute(
                    """
                    INSERT INTO trades (
                        buy_order_id,
                        sell_order_id,
                        price,
                        quantity,
                        engine_enter_ns,
                        engine_exit_ns,
                        latency_ns,
                        created_at_ns
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trade.buy_order_id,
                        trade.sell_order_id,
                        trade.price,
                        trade.quantity,
                        trade.engine_enter_ns,
                        trade.engine_exit_ns,
                        trade.latency_ns,
                        trade.engine_exit_ns,
                    ),
                )
                connection.commit()
                return True
            except sqlite3.Error as exc:
                logger.error(
                    "TradeLedger.save_trade: failed to persist trade "
                    "(buy_id=%s sell_id=%s): %s",
                    trade.buy_order_id,
                    trade.sell_order_id,
                    exc,
                )
                return False
            finally:
                connection.close()

    def save_trades(self, trades) -> int:
        """Persist multiple matched trades in one transaction.

        Returns the number of trades successfully persisted (0 on error).
        Database errors are logged and never re-raised.
        """
        if not trades:
            return 0

        valid_trades = []
        for t in trades:
            if isinstance(t, Trade):
                valid_trades.append(t)
            else:
                logger.warning(
                    "TradeLedger.save_trades: skipping invalid record type %s",
                    type(t).__name__,
                )

        if not valid_trades:
            return 0

        with self._lock:
            connection = self._connect()
            try:
                connection.executemany(
                    """
                    INSERT INTO trades (
                        buy_order_id,
                        sell_order_id,
                        price,
                        quantity,
                        engine_enter_ns,
                        engine_exit_ns,
                        latency_ns,
                        created_at_ns
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            t.buy_order_id,
                            t.sell_order_id,
                            t.price,
                            t.quantity,
                            t.engine_enter_ns,
                            t.engine_exit_ns,
                            t.latency_ns,
                            t.engine_exit_ns,
                        )
                        for t in valid_trades
                    ],
                )
                connection.commit()
                return len(valid_trades)
            except sqlite3.Error as exc:
                logger.error(
                    "TradeLedger.save_trades: failed to persist %d trade(s): %s",
                    len(valid_trades),
                    exc,
                )
                return 0
            finally:
                connection.close()

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def get_recent_trades(self, limit: int = 10):
        """Return the most recently persisted trades as raw row tuples."""
        connection = self._connect()
        try:
            cursor = connection.execute(
                """
                SELECT
                    trade_id,
                    buy_order_id,
                    sell_order_id,
                    price,
                    quantity,
                    engine_enter_ns,
                    engine_exit_ns,
                    latency_ns,
                    created_at_ns
                FROM trades
                ORDER BY trade_id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()
        except sqlite3.Error as exc:
            logger.error("TradeLedger.get_recent_trades: query failed: %s", exc)
            return []
        finally:
            connection.close()

    def count(self) -> int:
        """Return the total number of persisted trades."""
        connection = self._connect()
        try:
            cursor = connection.execute("SELECT COUNT(*) FROM trades")
            return cursor.fetchone()[0]
        except sqlite3.Error as exc:
            logger.error("TradeLedger.count: query failed: %s", exc)
            return 0
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        """No-op: connections are closed after each operation."""
        return None