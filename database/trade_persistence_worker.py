import queue
import threading

from engine.matching_engine import Trade
from database.trade_ledger import TradeLedger


class TradePersistenceWorker:
    """
    Background worker that asynchronously persists matched trades.
    """

    def __init__(self, database_path="trades.db"):
        self.ledger = TradeLedger(database_path)

        self._queue = queue.Queue()
        self._stop_event = threading.Event()

        self._worker = threading.Thread(
            target=self._run,
            name="trade-persistence-worker",
            daemon=True,
        )

        self._worker.start()

    def submit(self, trade: Trade):
        """Queue a matched trade for asynchronous persistence."""

        self._queue.put(trade)

    def submit_many(self, trades):
        """Queue multiple matched trades."""

        for trade in trades:
            self.submit(trade)

    def _run(self):
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                trade = self._queue.get(
                    timeout=0.1
                )
            except queue.Empty:
                continue

            try:
                self.ledger.save_trade(trade)
            finally:
                self._queue.task_done()

    def flush(self):
        """Wait until all queued trades are persisted."""

        self._queue.join()

    def pending(self):
        """Return the number of trades waiting for persistence."""

        return self._queue.qsize()

    def stop(self):
        """Flush pending trades and stop the worker."""

        self._stop_event.set()

        self.flush()

        self._worker.join()

        self.ledger.close()