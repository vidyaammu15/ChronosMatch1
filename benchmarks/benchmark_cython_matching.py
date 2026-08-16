import time

import numpy as np

from engine.cython_matcher import process_batch


ORDER_COUNT = 100_000
RUNS = 5


def create_orders():
    order_ids = np.arange(
        1,
        ORDER_COUNT + 1,
        dtype=np.uint64,
    )

    sides = np.where(
        order_ids % 2 == 1,
        1,
        2,
    ).astype(np.uint64)

    prices = np.full(
        ORDER_COUNT,
        65000,
        dtype=np.uint64,
    )

    quantities = np.ones(
        ORDER_COUNT,
        dtype=np.uint64,
    )

    return (
        order_ids,
        sides,
        prices,
        quantities,
    )


def run_benchmark():
    orders = create_orders()

    results = []

    print("=== Cython C-Level Matching Benchmark ===")
    print()
    print(f"Orders per run: {ORDER_COUNT}")
    print(f"Benchmark runs : {RUNS}")
    print()

    for run in range(1, RUNS + 1):
        start = time.perf_counter_ns()

        trades = process_batch(*orders)

        elapsed_ns = (
            time.perf_counter_ns() - start
        )

        elapsed_seconds = elapsed_ns / 1_000_000_000

        throughput = (
            ORDER_COUNT / elapsed_seconds
        )

        latency_us = (
            elapsed_ns / ORDER_COUNT / 1000
        )

        results.append(
            (
                throughput,
                latency_us,
            )
        )

        print(
            f"Run {run}: "
            f"{throughput:.2f} orders/sec | "
            f"{latency_us:.3f} us"
        )

        assert trades == ORDER_COUNT // 2

    average_throughput = sum(
        result[0] for result in results
    ) / RUNS

    average_latency = sum(
        result[1] for result in results
    ) / RUNS

    best_throughput = max(
        result[0] for result in results
    )

    best_latency = min(
        result[1] for result in results
    )

    print()
    print("=== Cython Benchmark Summary ===")
    print()
    print(
        f"Orders processed : {ORDER_COUNT}"
    )
    print(
        f"Trades generated : {ORDER_COUNT // 2}"
    )
    print(
        f"Average throughput: "
        f"{average_throughput:.2f} orders/sec"
    )
    print(
        f"Best throughput   : "
        f"{best_throughput:.2f} orders/sec"
    )
    print(
        f"Average latency   : "
        f"{average_latency:.3f} us"
    )
    print(
        f"Best latency      : "
        f"{best_latency:.3f} us"
    )

    print()
    print("Cython C-level benchmark completed successfully.")


if __name__ == "__main__":
    run_benchmark()
