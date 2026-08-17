import os
import tempfile
import time

from engine.matching_engine import Trade
from database.trade_persistence_worker import TradePersistenceWorker


def create_trade(trade_id):
    now = time.perf_counter_ns()

    return Trade(
        buy_order_id=trade_id * 2 - 1,
        sell_order_id=trade_id * 2,
        price=65000,
        quantity=1,
        engine_enter_ns=now,
        engine_exit_ns=now + 500,
        latency_ns=500,
    )


def cleanup_database(database_path):
    """Remove the temporary database safely on Windows."""

    for _ in range(10):
        try:
            if os.path.exists(database_path):
                os.remove(database_path)

            return

        except PermissionError:
            time.sleep(0.1)

    raise PermissionError(
        f"Could not remove temporary database: "
        f"{database_path}"
    )


def main():
    database_path = os.path.join(
        tempfile.gettempdir(),
        "chronosmatch_week4_test.db",
    )

    cleanup_database(database_path)

    worker = TradePersistenceWorker(
        database_path=database_path
    )

    trades = [
        create_trade(i)
        for i in range(1, 1001)
    ]

    start = time.perf_counter_ns()

    worker.submit_many(trades)

    print("=== Week 4 Trade Persistence Verification ===")
    print()
    print(f"Trades submitted : {len(trades)}")
    print(
        f"Pending before flush: "
        f"{worker.pending()}"
    )

    worker.flush()

    elapsed_ns = (
        time.perf_counter_ns() - start
    )

    persisted = worker.ledger.count()

    print(
        f"Trades persisted : {persisted}"
    )

    print(
        f"Persistence time: "
        f"{elapsed_ns / 1_000_000:.3f} ms"
    )

    assert persisted == len(trades)

    worker.stop()

    print()
    print("VERIFICATION PASSED")
    print(
        "Background worker successfully persisted "
        "all matched trades to SQLite."
    )

    cleanup_database(database_path)


if __name__ == "__main__":
    main()