import sqlite3
import threading
from pathlib import Path

from engine.matching_engine import Trade


class TradeLedger:
    """Persistent SQLite ledger for matched trades."""

    def __init__(self, database_path="trades.db"):
        self.database_path = Path(database_path)
        self._lock = threading.Lock()

        self._initialize()

    def _connect(self):
        return sqlite3.connect(
            self.database_path,
            check_same_thread=False,
        )

    def _initialize(self):
        connection = self._connect()

        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buy_order_id INTEGER NOT NULL,
                    sell_order_id INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    engine_enter_ns INTEGER NOT NULL,
                    engine_exit_ns INTEGER NOT NULL,
                    latency_ns INTEGER NOT NULL,
                    created_at_ns INTEGER NOT NULL
                )
                """
            )

            connection.commit()

        finally:
            connection.close()

    def save_trade(self, trade: Trade):
        """Persist one matched trade."""

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

            finally:
                connection.close()

    def save_trades(self, trades):
        """Persist multiple matched trades in one transaction."""

        if not trades:
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
                            trade.buy_order_id,
                            trade.sell_order_id,
                            trade.price,
                            trade.quantity,
                            trade.engine_enter_ns,
                            trade.engine_exit_ns,
                            trade.latency_ns,
                            trade.engine_exit_ns,
                        )
                        for trade in trades
                    ],
                )

                connection.commit()

            finally:
                connection.close()

        return len(trades)

    def get_recent_trades(self, limit=10):
        """Return the most recently persisted trades."""

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

        finally:
            connection.close()

    def count(self):
        """Return the total number of persisted trades."""

        connection = self._connect()

        try:
            cursor = connection.execute(
                "SELECT COUNT(*) FROM trades"
            )

            return cursor.fetchone()[0]

        finally:
            connection.close()

    def close(self):
        """Close the ledger."""

        return None