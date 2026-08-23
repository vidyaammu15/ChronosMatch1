import asyncio
import time

from core.types import Order, OrderSide


class MarketFirehose:
    def __init__(self, rate: int = 1000):
        self.rate = rate
        self.order_id = 0

    def generate_order(self) -> Order:
        self.order_id += 1
        is_buy = (self.order_id % 2 == 1)
        
        # 80% passive orders to populate book, 20% aggressive orders to trigger trades
        is_aggressive = ((self.order_id % 5) == 0)

        if is_buy:
            side = OrderSide.BUY
            if is_aggressive:
                price = 65010 + ((self.order_id * 13) % 40)
            else:
                price = 64990 - ((self.order_id * 17) % 200)
        else:
            side = OrderSide.SELL
            if is_aggressive:
                price = 64990 - ((self.order_id * 11) % 40)
            else:
                price = 65010 + ((self.order_id * 19) % 200)

        quantity = 100 + ((self.order_id * 37) % 900)

        return Order(
            order_id=self.order_id,
            side=side,
            price=price,
            quantity=quantity,
            timestamp=time.perf_counter_ns(),
        )

    async def stream(self, count: int):
        for _ in range(count):
            yield self.generate_order()


async def main():
    firehose = MarketFirehose()

    count = 1000

    start = time.perf_counter()

    received = 0

    async for order in firehose.stream(count):
        received += 1

    elapsed = time.perf_counter() - start

    throughput = (
        received / elapsed
        if elapsed > 0
        else 0
    )

    print(f"Orders generated: {received}")
    print(f"Elapsed time: {elapsed:.6f} seconds")
    print(f"Throughput: {throughput:.2f} orders/second")


if __name__ == "__main__":
    asyncio.run(main())