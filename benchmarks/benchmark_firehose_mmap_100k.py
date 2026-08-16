import asyncio
import multiprocessing as mp
import os
import time

from ipc.mmap_ring_buffer import MMapRingBuffer
from simulator.market_firehose import MarketFirehose


FILE_PATH = "chronosmatch_week1_firehose.bin"
CAPACITY = 131072
ORDER_COUNT = 100_000


def producer(result_queue, ready_event):
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )

    ready_event.set()

    produced = 0

    async def produce():
        nonlocal produced

        firehose = MarketFirehose(
            rate=100_000
        )

        async for order in firehose.stream(ORDER_COUNT):
            while buffer.is_full():
                await asyncio.sleep(0)

            buffer.write(order)
            produced += 1

    try:
        asyncio.run(produce())
        result_queue.put(produced)

    finally:
        buffer.close()


def consumer(result_queue, ready_event):
    ready_event.wait()

    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    consumed = 0

    try:
        while consumed < ORDER_COUNT:
            if buffer.is_empty():
                continue

            buffer.read()
            consumed += 1

        result_queue.put(consumed)

    finally:
        buffer.close()


def main():
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

    producer_queue = mp.Queue()
    consumer_queue = mp.Queue()

    ready_event = mp.Event()

    producer_process = mp.Process(
        target=producer,
        args=(producer_queue, ready_event),
    )

    consumer_process = mp.Process(
        target=consumer,
        args=(consumer_queue, ready_event),
    )

    start = time.perf_counter_ns()

    consumer_process.start()
    producer_process.start()

    producer_process.join()
    consumer_process.join()

    elapsed_ns = time.perf_counter_ns() - start

    produced = producer_queue.get()
    consumed = consumer_queue.get()

    elapsed_seconds = elapsed_ns / 1_000_000_000

    throughput = (
        consumed / elapsed_seconds
        if elapsed_seconds > 0
        else 0
    )

    latency_us = (
        elapsed_ns / consumed / 1000
        if consumed > 0
        else 0
    )

    print("=== Week 1 Firehose + mmap IPC Verification ===")
    print()
    print("Market Firehose")
    print("        ?")
    print("mmap SPSC Ring Buffer")
    print("        ?")
    print("Consumer")
    print()
    print(f"Orders produced : {produced}")
    print(f"Orders consumed : {consumed}")
    print(f"Elapsed time    : {elapsed_seconds:.6f} seconds")
    print(f"Throughput      : {throughput:.2f} orders/second")
    print(f"Average latency : {latency_us:.3f} microseconds")
    print()

    if produced != ORDER_COUNT:
        raise RuntimeError(
            f"Expected {ORDER_COUNT} produced orders, got {produced}"
        )

    if consumed != ORDER_COUNT:
        raise RuntimeError(
            f"Expected {ORDER_COUNT} consumed orders, got {consumed}"
        )

    print("VERIFICATION PASSED")
    print("Market Firehose successfully transferred")
    print("100,000 orders through the mmap SPSC IPC bus.")

    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)


if __name__ == "__main__":
    mp.freeze_support()
    main()
