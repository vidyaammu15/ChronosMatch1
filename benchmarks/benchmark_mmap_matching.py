import multiprocessing as mp
import os
import time

from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine
from ipc.mmap_ring_buffer import MMapRingBuffer


FILE_PATH = "chronosmatch_week3_matching.bin"
CAPACITY = 131072
ORDER_COUNT = 100000
BATCH_SIZE = 1024


def producer():
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )

    produced = 0

    try:
        while produced < ORDER_COUNT:
            batch_count = min(
                BATCH_SIZE,
                ORDER_COUNT - produced,
            )

            orders = []

            for i in range(batch_count):
                order_id = produced + i + 1

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

            written = buffer.write_batch(orders)
            produced += written

    finally:
        buffer.close()


def consumer(result_queue):
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    engine = MatchingEngine()
    consumed = 0
    trades = 0

    try:
        while consumed < ORDER_COUNT:
            if buffer.is_empty():
                continue

            order = buffer.read()

            generated_trades = engine.process_order(order)

            consumed += 1
            trades += len(generated_trades)

        result_queue.put(
            (
                consumed,
                trades,
            )
        )

    finally:
        buffer.close()


def main():
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

    result_queue = mp.Queue()

    consumer_process = mp.Process(
        target=consumer,
        args=(result_queue,),
    )

    producer_process = mp.Process(
        target=producer,
    )

    start = time.perf_counter()

    consumer_process.start()
    producer_process.start()

    producer_process.join()
    consumer_process.join()

    elapsed = time.perf_counter() - start

    consumed, trades = result_queue.get()

    throughput = (
        consumed / elapsed
        if elapsed > 0
        else 0
    )

    latency_us = (
        elapsed / consumed * 1_000_000
        if consumed > 0
        else 0
    )

    print("=== mmap IPC Matching Benchmark ===")
    print()
    print("Producer Process")
    print("        ?")
    print("mmap SPSC Ring Buffer")
    print("        ?")
    print("Matching Engine Process")
    print()

    print(f"Orders consumed : {consumed}")
    print(f"Trades generated: {trades}")
    print(f"Elapsed time    : {elapsed:.6f} seconds")
    print(f"Throughput      : {throughput:.2f} orders/second")
    print(f"Avg latency     : {latency_us:.3f} microseconds")
    print()
    print("IPC model       : mmap SPSC")
    print("Pickle for order transfer: NO")

    if consumed != ORDER_COUNT:
        raise RuntimeError(
            f"Expected {ORDER_COUNT} orders, "
            f"received {consumed}"
        )

    print()
    print("mmap matching benchmark completed successfully.")

    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)


if __name__ == "__main__":
    mp.freeze_support()
    main()
