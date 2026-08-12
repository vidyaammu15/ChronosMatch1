import asyncio
import time

from ipc.mmap_ring_buffer import MMapRingBuffer
from simulator.market_firehose import MarketFirehose


FILE_PATH = "chronosmatch_firehose.bin"
CAPACITY = 4096
ORDER_COUNT = 100000
BATCH_SIZE = 256


async def produce_orders():
    firehose = MarketFirehose()

    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )

    produced = 0

    try:
        while produced < ORDER_COUNT:

            # Check available space in the ring buffer.
            head = buffer.head
            tail = buffer.tail

            available = CAPACITY - (head - tail)

            if available <= 0:
                # Yield only when the consumer needs to free space.
                await asyncio.sleep(0)
                continue

            batch_count = min(
                BATCH_SIZE,
                available,
                ORDER_COUNT - produced,
            )

            orders = [
                firehose.generate_order()
                for _ in range(batch_count)
            ]

            written = buffer.write_batch(orders)

            produced += written

        return produced

    finally:
        buffer.close()


def main():
    start = time.perf_counter()

    produced = asyncio.run(
        produce_orders()
    )

    elapsed = time.perf_counter() - start

    throughput = (
        produced / elapsed
        if elapsed > 0
        else 0
    )

    print(f"Orders produced: {produced}")
    print(f"Elapsed time: {elapsed:.6f} seconds")
    print(f"Throughput: {throughput:.2f} orders/second")


if __name__ == "__main__":
    main()