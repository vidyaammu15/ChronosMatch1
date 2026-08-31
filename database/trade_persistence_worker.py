import logging
import queue
import threading

from engine.matching_engine import Trade
from database.trade_ledger import TradeLedger

logger = logging.getLogger(__name__)


class TradePersistenceWorker:
    """Background worker that asynchronously persists matched trades.

    Design goals
    ------------
    * Non-blocking: ``submit`` and ``submit_many`` never wait for the DB.
    * Resilient: persistence failures are logged but never crash the engine.
    * Safe shutdown: ``stop`` drains the queue before returning.
    * Transparent: ``pending`` and ``flush`` let callers inspect/wait.
    """

    def __init__(self, database_path: str = "trades.db"):
        self.ledger = TradeLedger(database_path)

        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()

        self._worker = threading.Thread(
            target=self._run,
            name="trade-persistence-worker",
            daemon=True,
        )
        self._worker.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(self, trade: Trade) -> None:
        """Queue a matched trade for asynchronous persistence.

        This call is non-blocking and safe to call from the hot path.
        """
        if not isinstance(trade, Trade):
            logger.warning(
                "TradePersistenceWorker.submit: ignoring invalid record type %s",
                type(trade).__name__,
            )
            return
        self._queue.put(trade)

    def submit_many(self, trades) -> None:
        """Queue multiple matched trades for asynchronous persistence."""
        for trade in trades:
            self.submit(trade)

    def flush(self) -> None:
        """Block until all currently queued trades have been persisted."""
        self._queue.join()

    def pending(self) -> int:
        """Return the approximate number of trades waiting for persistence."""
        return self._queue.qsize()

    def stop(self) -> None:
        """Signal the worker to stop, flush remaining trades, then join."""
        self._stop_event.set()
        # Drain whatever is still in the queue before joining.
        self._queue.join()
        self._worker.join()
        self.ledger.close()

    # ------------------------------------------------------------------
    # Worker loop
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Background loop: dequeue trades and persist them one by one."""
        while True:
            # Exit only when stop has been requested AND the queue is empty.
            if self._stop_event.is_set() and self._queue.empty():
                break

            try:
                trade = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue

            try:
                success = self.ledger.save_trade(trade)
                if not success:
                    # save_trade already logged the reason; the trade is
                    # dropped intentionally rather than re-queued to avoid
                    # an infinite retry loop on a broken DB.
                    logger.warning(
                        "TradePersistenceWorker: trade (buy_id=%s sell_id=%s) "
                        "was not persisted and will be dropped.",
                        trade.buy_order_id,
                        trade.sell_order_id,
                    )
            except Exception as exc:
                # Belt-and-suspenders: catch any unexpected error so the
                # worker thread never dies silently.
                logger.error(
                    "TradePersistenceWorker: unexpected error persisting trade: %s",
                    exc,
                    exc_info=True,
                )
            finally:
                # Always mark the task done so flush() / stop() can unblock.
                self._queue.task_done()