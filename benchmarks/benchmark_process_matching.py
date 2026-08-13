import multiprocessing as mp
import time

from core.ctypes_types import order_to_c, c_to_order
from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine


ORDER_COUNT = 100000


def create_orders():
    orders = []

    for order_id in range(1, ORDER_COUNT + 1):
        side = (
            OrderSide.BUY
            if order_id % 2 == 1
            else OrderSide.SELL
        )

        orders.append(
            Order(
                order_id=order_id,
                side=side,
                price=65000,
                quantity=1,
                timestamp=order_id,
            )
        )

    return orders


def matching_worker(input_queue, output_queue):
    """
    Runs in a separate Python process.

    Because this is a separate process, it has its own
    Python interpreter and its own GIL.
    """

    engine = MatchingEngine()

    processed = 0
    trades = 0

    while True:
        c_order = input_queue.get()

        if c_order is None:
            break

        order = c_to_order(c_order)

        generated_trades = engine.process_order(order)

        processed += 1
        trades += len(generated_trades)

    output_queue.put(
        (processed, trades)
    )


def main():
    input_queue = mp.Queue(
        maxsize=4096
    )

    output_queue = mp.Queue()

    process = mp.Process(
        target=matching_worker,
        args=(
            input_queue,
            output_queue,
        ),
    )

    process.start()

    orders = create_orders()

    start = time.perf_counter()

    for order in orders:
        c_order = order_to_c(order)
        input_queue.put(c_order)

    input_queue.put(None)

    processed, trades = output_queue.get()

    process.join()

    elapsed = time.perf_counter() - start

    throughput = (
        processed / elapsed
        if elapsed > 0
        else 0
    )

    latency_us = (
        elapsed / processed * 1_000_000
        if processed > 0
        else 0
    )

    print("=== Process-Isolated Matching Benchmark ===")
    print(f"Orders processed: {processed}")
    print(f"Trades generated: {trades}")
    print(f"Elapsed time: {elapsed:.6f} seconds")
    print(f"Throughput: {throughput:.2f} orders/second")
    print(f"Average latency: {latency_us:.3f} microseconds")
    print("Execution model: separate Python process")


if __name__ == "__main__":
    mp.freeze_support()
    main()
