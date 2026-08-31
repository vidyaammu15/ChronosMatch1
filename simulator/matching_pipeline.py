"""matching_pipeline.py

Simulation pipeline that wires together:
  - MarketFirehose  (order generation)
  - MatchingEngine  (order matching)
  - TradePersistenceWorker (async background persistence — Week 4)

The matching engine stays responsive: persistence is handed off to
a background thread and never blocks the matching loop.
"""
from engine.matching_engine import MatchingEngine
from simulator.market_firehose import MarketFirehose
from database.trade_persistence_worker import TradePersistenceWorker


def run_matching_pipeline(
    order_count: int = 100,
    database_path: str = "trades.db",
    persist: bool = True,
) -> list:
    """Run a simulation of *order_count* orders through the matching engine.

    Parameters
    ----------
    order_count:
        Number of synthetic orders to generate and process.
    database_path:
        Path to the SQLite ledger file.  Ignored when *persist* is False.
    persist:
        When True (default) matched trades are asynchronously persisted to
        SQLite via a background worker.  Set to False in unit tests that do
        not need database I/O.

    Returns
    -------
    list[Trade]
        All trades that were matched during the run.
    """
    firehose = MarketFirehose()
    engine = MatchingEngine()
    worker = TradePersistenceWorker(database_path) if persist else None

    trades: list = []

    for _ in range(order_count):
        order = firehose.generate_order()
        new_trades = engine.process_order(order)

        if new_trades:
            trades.extend(new_trades)

            # Hand off to the background worker — non-blocking.
            if worker is not None:
                worker.submit_many(new_trades)

    # Wait for all queued persistence to finish before returning.
    if worker is not None:
        worker.stop()

    return trades


if __name__ == "__main__":
    trades = run_matching_pipeline(100)

    print("Matching pipeline completed.")
    print(f"Trades generated: {len(trades)}")