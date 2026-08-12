import os
import time

from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine
from ipc.mmap_ring_buffer import MMapRingBuffer


FILE_PATH = "benchmark_ring.bin"
CAPACITY = 1024


def create_order(order_id):
    return Order(
        order_id=order_id,
        side=(
            OrderSide.BUY
            if order_id % 2 == 1
            else OrderSide.SELL
        ),
        price=65000,
        quantity=1,
        timestamp=time.perf_counter_ns(),
    )


def benchmark(order_count=10000):
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )

    engine = MatchingEngine()

    trades = 0

    start = time.perf_counter_ns()

    try:
        for order_id in range(1, order_count + 1):
            order = create_order(order_id)

            # Producer side
            buffer.write(order)

            # Consumer side
            received_order = buffer.read()

            # Matching engine
            generated_trades = engine.process_order(
                received_order
            )

            trades += len(generated_trades)

    finally:
        buffer.close()

        if os.path.exists(FILE_PATH):
            os.remove(FILE_PATH)

    elapsed_ns = time.perf_counter_ns() - start
    elapsed_seconds = elapsed_ns / 1_000_000_000

    throughput = (
        order_count / elapsed_seconds
        if elapsed_seconds > 0
        else 0
    )

    average_latency_us = (
        elapsed_ns / order_count / 1_000
        if order_count > 0
        else 0
    )

    print("=== mmap End-to-End Benchmark ===")
    print(f"Orders processed: {order_count}")
    print(f"Trades generated: {trades}")
    print(f"Elapsed time: {elapsed_seconds:.6f} seconds")
    print(f"Throughput: {throughput:.2f} orders/second")
    print(f"Average latency: {average_latency_us:.3f} microseconds")


if __name__ == "__main__":
    benchmark(10000)