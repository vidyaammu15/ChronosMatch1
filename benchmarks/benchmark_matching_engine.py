import time

from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine


def create_order(order_id, side, price, quantity):
    return Order(
        order_id=order_id,
        side=side,
        price=price,
        quantity=quantity,
        timestamp=time.perf_counter_ns(),
    )


def benchmark(order_count=10000):
    engine = MatchingEngine()

    start = time.perf_counter_ns()

    trades = 0

    for order_id in range(1, order_count + 1):
        if order_id % 2 == 1:
            side = OrderSide.BUY
            price = 65000
        else:
            side = OrderSide.SELL
            price = 65000

        order = create_order(
            order_id,
            side,
            price,
            1,
        )

        generated_trades = engine.process_order(order)
        trades += len(generated_trades)

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

    print("=== Matching Engine Benchmark ===")
    print(f"Orders processed: {order_count}")
    print(f"Trades generated: {trades}")
    print(f"Elapsed time: {elapsed_seconds:.6f} seconds")
    print(f"Throughput: {throughput:.2f} orders/second")
    print(f"Average latency: {average_latency_us:.3f} microseconds")


if __name__ == "__main__":
    for count in [1000, 10000, 100000]:
        print()
        benchmark(count)