import multiprocessing as mp
import os
import statistics
import tempfile
import time

import numpy as np

from core.types import Order
from database.trade_persistence_worker import TradePersistenceWorker
from engine.cython_matcher import process_batch
from engine.matching_engine import MatchingEngine
from ipc.mmap_ring_buffer import MMapRingBuffer
from simulator.market_firehose import MarketFirehose


ORDER_COUNT = 1000
CYTHON_ORDER_COUNT = 100_000
RING_CAPACITY = 4096

IPC_FILE = os.path.join(
    tempfile.gettempdir(),
    "chronosmatch_final_review.bin",
)

DATABASE_FILE = os.path.join(
    tempfile.gettempdir(),
    "chronosmatch_final_review.db",
)


def producer(start_event, result_queue):
    buffer = MMapRingBuffer(
        file_path=IPC_FILE,
        capacity=RING_CAPACITY,
        create=False,
    )

    firehose = MarketFirehose()

    produced = 0

    try:
        start_event.wait()

        start_ns = time.perf_counter_ns()

        while produced < ORDER_COUNT:
            if buffer.is_full():
                continue

            buffer.write(
                firehose.generate_order()
            )

            produced += 1

        elapsed_ns = (
            time.perf_counter_ns()
            - start_ns
        )

        result_queue.put(
            (
                "producer",
                produced,
                elapsed_ns,
            )
        )

    finally:
        buffer.close()


def consumer(start_event, result_queue):
    buffer = MMapRingBuffer(
        file_path=IPC_FILE,
        capacity=RING_CAPACITY,
        create=False,
    )

    engine = MatchingEngine()

    worker = TradePersistenceWorker(
        database_path=DATABASE_FILE
    )

    consumed = 0
    trades_generated = 0
    latencies = []

    first_order_id = None
    last_order_id = None
    fifo_ok = True

    try:
        start_event.wait()

        pipeline_start_ns = time.perf_counter_ns()

        while consumed < ORDER_COUNT:

            if buffer.is_empty():
                continue

            order = buffer.read()

            if first_order_id is None:
                first_order_id = order.order_id

            if (
                last_order_id is not None
                and order.order_id != last_order_id + 1
            ):
                fifo_ok = False

            last_order_id = order.order_id

            trades = engine.process_order(order)

            consumed += 1
            trades_generated += len(trades)

            if trades:
                for trade in trades:
                    latencies.append(
                        trade.latency_ns
                    )

                worker.submit_many(trades)

        matching_end_ns = time.perf_counter_ns()

        worker.flush()

        persistence_end_ns = time.perf_counter_ns()

        persisted = worker.ledger.count()

        result_queue.put(
            (
                "consumer",
                consumed,
                trades_generated,
                persisted,
                first_order_id,
                last_order_id,
                fifo_ok,
                latencies,
                pipeline_start_ns,
                matching_end_ns,
                persistence_end_ns,
            )
        )

    finally:
        worker.stop()
        buffer.close()


def run_cython_verification():
    order_ids = np.arange(
        1,
        CYTHON_ORDER_COUNT + 1,
        dtype=np.uint64,
    )

    sides = np.where(
        order_ids % 2 == 1,
        1,
        2,
    ).astype(np.uint64)

    prices = np.full(
        CYTHON_ORDER_COUNT,
        65000,
        dtype=np.uint64,
    )

    quantities = np.ones(
        CYTHON_ORDER_COUNT,
        dtype=np.uint64,
    )

    start_ns = time.perf_counter_ns()

    trades = process_batch(
        order_ids,
        sides,
        prices,
        quantities,
    )

    elapsed_ns = (
        time.perf_counter_ns()
        - start_ns
    )

    expected_trades = (
        CYTHON_ORDER_COUNT // 2
    )

    assert trades == expected_trades

    latency_us = (
        elapsed_ns
        / CYTHON_ORDER_COUNT
        / 1000
    )

    throughput = (
        CYTHON_ORDER_COUNT
        / (elapsed_ns / 1_000_000_000)
    )

    return (
        trades,
        latency_us,
        throughput,
    )


def cleanup():
    for path in (
        IPC_FILE,
        DATABASE_FILE,
        DATABASE_FILE + "-wal",
        DATABASE_FILE + "-shm",
    ):
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                pass


def main():
    cleanup()

    print("=" * 60)
    print("       CHRONOSMATCH FINAL REVIEW")
    print("=" * 60)
    print()

    # ---------------------------------------------------------
    # Prepare mmap IPC
    # ---------------------------------------------------------

    buffer = MMapRingBuffer(
        file_path=IPC_FILE,
        capacity=RING_CAPACITY,
        create=True,
    )

    buffer.close()

    # ---------------------------------------------------------
    # Start producer and consumer
    # ---------------------------------------------------------

    start_event = mp.Event()
    result_queue = mp.Queue()

    producer_process = mp.Process(
        target=producer,
        args=(
            start_event,
            result_queue,
        ),
    )

    consumer_process = mp.Process(
        target=consumer,
        args=(
            start_event,
            result_queue,
        ),
    )

    producer_process.start()
    consumer_process.start()

    overall_start_ns = time.perf_counter_ns()

    start_event.set()

    results = [
        result_queue.get(),
        result_queue.get(),
    ]

    producer_process.join()
    consumer_process.join()

    overall_elapsed_ns = (
        time.perf_counter_ns()
        - overall_start_ns
    )

    producer_result = next(
        result
        for result in results
        if result[0] == "producer"
    )

    consumer_result = next(
        result
        for result in results
        if result[0] == "consumer"
    )

    (
        _,
        produced,
        producer_elapsed_ns,
    ) = producer_result

    (
        _,
        consumed,
        trades_generated,
        persisted,
        first_order_id,
        last_order_id,
        fifo_ok,
        latencies,
        pipeline_start_ns,
        matching_end_ns,
        persistence_end_ns,
    ) = consumer_result

    # ---------------------------------------------------------
    # Cython verification
    # ---------------------------------------------------------

    (
        cython_trades,
        cython_latency_us,
        cython_throughput,
    ) = run_cython_verification()

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

    producer_seconds = (
        producer_elapsed_ns
        / 1_000_000_000
    )

    overall_seconds = (
        overall_elapsed_ns
        / 1_000_000_000
    )

    producer_throughput = (
        produced / producer_seconds
        if producer_seconds > 0
        else 0
    )

    end_to_end_throughput = (
        consumed / overall_seconds
        if overall_seconds > 0
        else 0
    )

    matching_elapsed_ns = (
        matching_end_ns
        - pipeline_start_ns
    )

    persistence_elapsed_ns = (
        persistence_end_ns
        - matching_end_ns
    )

    matching_latency_us = (
        matching_elapsed_ns
        / consumed
        / 1000
    )

    persistence_ms = (
        persistence_elapsed_ns
        / 1_000_000
    )

    average_trade_latency_us = (
        statistics.mean(latencies) / 1000
        if latencies
        else 0
    )

    best_trade_latency_us = (
        min(latencies) / 1000
        if latencies
        else 0
    )

    sub_ms = (
        cython_latency_us < 1000
        and matching_latency_us < 1000
    )

    # ---------------------------------------------------------
    # Final report
    # ---------------------------------------------------------

    print("SYSTEM PIPELINE")
    print(
        "Market Firehose"
        " -> mmap SPSC IPC"
        " -> Matching Engine"
        " -> Persistence Worker"
        " -> SQLite"
    )
    print()

    print("IPC")
    print("-" * 60)
    print("IPC mechanism       : mmap SPSC Ring Buffer")
    print("Serialization       : Fixed binary order format")
    print("Pickle transfer     : NO")
    print("Python processes    : 2")
    print("Orders produced     :", produced)
    print("Orders consumed     :", consumed)
    print("First order ID      :", first_order_id)
    print("Last order ID       :", last_order_id)
    print("FIFO ordering       :", fifo_ok)
    print(
        "Producer throughput : "
        f"{producer_throughput:.2f} orders/sec"
    )
    print(
        "End-to-end throughput: "
        f"{end_to_end_throughput:.2f} orders/sec"
    )
    print()

    print("MATCHING ENGINE")
    print("-" * 60)
    print("Python order-book matching : ENABLED")
    print("Trades generated            :", trades_generated)
    print(
        "Average trade latency       : "
        f"{average_trade_latency_us:.3f} us"
    )
    print(
        "Best trade latency          : "
        f"{best_trade_latency_us:.3f} us"
    )
    print(
        "Integrated matching latency: "
        f"{matching_latency_us:.3f} us/order"
    )
    print()

    print("CYTHON C-LEVEL ENGINE")
    print("-" * 60)
    print(
        "Orders processed : "
        f"{CYTHON_ORDER_COUNT}"
    )
    print(
        "Trades generated : "
        f"{cython_trades}"
    )
    print(
        "Average latency  : "
        f"{cython_latency_us:.3f} us/order"
    )
    print(
        "Throughput       : "
        f"{cython_throughput:.2f} orders/sec"
    )
    print()

    print("PERSISTENCE")
    print("-" * 60)
    print("Background worker : ENABLED")
    print("SQLite ledger     : ENABLED")
    print("Trades persisted  :", persisted)
    print(
        "Persistence time  : "
        f"{persistence_ms:.3f} ms"
    )
    print()

    print("FINAL VERIFICATION")
    print("-" * 60)

    checks = [
        (
            "IPC transferred all orders",
            produced == ORDER_COUNT
            and consumed == ORDER_COUNT,
        ),
        (
            "FIFO ordering preserved",
            fifo_ok,
        ),
        (
            "Trades were generated",
            trades_generated > 0,
        ),
        (
            "All trades persisted",
            persisted == trades_generated,
        ),
        (
            "Cython matching verified",
            cython_trades
            == CYTHON_ORDER_COUNT // 2,
        ),
        (
            "Sub-millisecond matching",
            sub_ms,
        ),
    ]

    all_passed = True

    for name, passed in checks:
        print(
            f"[{'PASS' if passed else 'FAIL'}] "
            f"{name}"
        )

        if not passed:
            all_passed = False

    print()

    if not all_passed:
        raise RuntimeError(
            "FINAL REVIEW FAILED"
        )

    print("=" * 60)
    print("       FINAL REVIEW PASSED")
    print("=" * 60)

    cleanup()


if __name__ == "__main__":
    mp.freeze_support()
    main()