import asyncio
import time

from core.types import Order, OrderSide


class MarketFirehose:
    def __init__(self, rate: int = 1000):
        self.rate = rate
        self.order_id = 0

    def generate_order(self) -> Order:
        self.order_id += 1

        return Order(
            order_id=self.order_id,
            side=(
                OrderSide.BUY
                if self.order_id % 2
                else OrderSide.SELL
            ),
            price=65000 + (self.order_id % 100),
            quantity=1 + (self.order_id % 10),
            timestamp=time.perf_counter_ns(),
        )

    async def stream(self, count: int):
        for _ in range(count):
            yield self.generate_order()

            # Give the event loop a chance to run other tasks.
            await asyncio.sleep(0)


async def main():
    firehose = MarketFirehose()

    count = 1000

    start = time.perf_counter()

    received = 0

    async for order in firehose.stream(count):
        received += 1

    elapsed = time.perf_counter() - start

    throughput = received / elapsed if elapsed > 0 else 0

    print(f"Orders generated: {received}")
    print(f"Elapsed time: {elapsed:.6f} seconds")
    print(f"Throughput: {throughput:.2f} orders/second")


if __name__ == "__main__":
    asyncio.run(main())