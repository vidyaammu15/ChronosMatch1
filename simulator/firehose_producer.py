import asyncio
import time

from ipc.mmap_ring_buffer import MMapRingBuffer
from simulator.market_firehose import MarketFirehose


FILE_PATH = "chronosmatch_firehose.bin"
CAPACITY = 2048
ORDER_COUNT = 1000


async def produce_orders():
    firehose = MarketFirehose()

    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )

    produced = 0

    try:
        async for order in firehose.stream(ORDER_COUNT):
            buffer.write(order)
            produced += 1

        return produced

    finally:
        buffer.close()


def main():
    start = time.perf_counter()

    produced = asyncio.run(produce_orders())

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