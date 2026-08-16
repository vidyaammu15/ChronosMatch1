import asyncio
import time

from simulator.market_firehose import MarketFirehose


ORDER_COUNT = 100_000
TARGET_RATE = 100_000


async def benchmark_firehose():
    firehose = MarketFirehose(
        rate=TARGET_RATE
    )

    generated = 0

    start = time.perf_counter_ns()

    async for order in firehose.stream(ORDER_COUNT):
        generated += 1

    elapsed_ns = time.perf_counter_ns() - start

    elapsed_seconds = elapsed_ns / 1_000_000_000

    throughput = (
        generated / elapsed_seconds
        if elapsed_seconds > 0
        else 0
    )

    latency_us = (
        elapsed_ns / generated / 1000
        if generated > 0
        else 0
    )

    print("=== Week 1 Market Firehose Benchmark ===")
    print()
    print(f"Orders generated : {generated}")
    print(f"Target rate      : {TARGET_RATE} orders/sec")
    print(f"Elapsed time     : {elapsed_seconds:.6f} seconds")
    print(f"Throughput       : {throughput:.2f} orders/sec")
    print(f"Average latency  : {latency_us:.3f} microseconds")
    print()

    if generated != ORDER_COUNT:
        raise RuntimeError(
            f"Expected {ORDER_COUNT} orders, "
            f"generated {generated}"
        )

    print("Firehose benchmark completed successfully.")


if __name__ == "__main__":
    asyncio.run(benchmark_firehose())
