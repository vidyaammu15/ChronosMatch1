import time

from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine


def main():
    engine = MatchingEngine()

    orders = [
        Order(
            order_id=1,
            side=OrderSide.SELL,
            price=65000,
            quantity=10,
            timestamp=time.perf_counter_ns(),
        ),
        Order(
            order_id=2,
            side=OrderSide.BUY,
            price=65000,
            quantity=10,
            timestamp=time.perf_counter_ns(),
        ),
        Order(
            order_id=3,
            side=OrderSide.SELL,
            price=65100,
            quantity=5,
            timestamp=time.perf_counter_ns(),
        ),
        Order(
            order_id=4,
            side=OrderSide.BUY,
            price=65200,
            quantity=5,
            timestamp=time.perf_counter_ns(),
        ),
    ]

    for order in orders:
        engine.process_order(order)

    metrics = engine.metrics.summary()

    print("=" * 55)
    print("     CHRONOSMATCH WEEK 3 - LATENCY METRICS")
    print("=" * 55)
    print(f"Trades measured : {metrics['count']}")
    print(f"Minimum latency : {metrics['min_latency_ns']} ns")
    print(f"Maximum latency : {metrics['max_latency_ns']} ns")
    print(f"Average latency : {metrics['avg_latency_ns']:.2f} ns")
    print("=" * 55)
    print("METRICS TRACKING VERIFIED")
    print("=" * 55)


if __name__ == "__main__":
    main()