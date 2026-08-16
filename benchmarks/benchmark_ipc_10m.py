import multiprocessing as mp
import os
import time

from ipc.mmap_ring_buffer import MMapRingBuffer
from simulator.market_firehose import MarketFirehose


FILE_PATH = "ipc_audit_10m.bin"
CAPACITY = 131072
ORDER_COUNT = 10_000_000


def producer(start_event, result_queue):
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    firehose = MarketFirehose()
    produced = 0

    try:
        start_event.wait()
        start = time.perf_counter_ns()

        while produced < ORDER_COUNT:
            if buffer.is_full():
                continue

            buffer.write(firehose.generate_order())
            produced += 1

        elapsed_ns = time.perf_counter_ns() - start

        result_queue.put(
            ("producer", produced, elapsed_ns)
        )

    finally:
        buffer.close()


def consumer(start_event, result_queue):
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    consumed = 0
    first_order_id = None
    last_order_id = None
    fifo_ok = True

    try:
        start_event.wait()
        start = time.perf_counter_ns()

        while consumed < ORDER_COUNT:
            if buffer.is_empty():
                continue

            order = buffer.read()
            consumed += 1

            if first_order_id is None:
                first_order_id = order.order_id

            if (
                last_order_id is not None
                and order.order_id != last_order_id + 1
            ):
                fifo_ok = False

            last_order_id = order.order_id

        elapsed_ns = time.perf_counter_ns() - start

        result_queue.put(
            (
                "consumer",
                consumed,
                elapsed_ns,
                first_order_id,
                last_order_id,
                fifo_ok,
            )
        )

    finally:
        buffer.close()


def main():
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )
    buffer.close()

    start_event = mp.Event()
    result_queue = mp.Queue()

    producer_process = mp.Process(
        target=producer,
        args=(start_event, result_queue),
    )

    consumer_process = mp.Process(
        target=consumer,
        args=(start_event, result_queue),
    )

    producer_process.start()
    consumer_process.start()

    overall_start = time.perf_counter_ns()

    start_event.set()

    results = [
        result_queue.get(),
        result_queue.get(),
    ]

    producer_process.join()
    consumer_process.join()

    overall_elapsed_ns = (
        time.perf_counter_ns() - overall_start
    )

    producer_result = next(
        result for result in results
        if result[0] == "producer"
    )

    consumer_result = next(
        result for result in results
        if result[0] == "consumer"
    )

    _, produced, producer_elapsed_ns = producer_result

    (
        _,
        consumed,
        consumer_elapsed_ns,
        first_order_id,
        last_order_id,
        fifo_ok,
    ) = consumer_result

    producer_seconds = producer_elapsed_ns / 1_000_000_000
    consumer_seconds = consumer_elapsed_ns / 1_000_000_000
    overall_seconds = overall_elapsed_ns / 1_000_000_000

    producer_throughput = (
        produced / producer_seconds
        if producer_seconds > 0
        else 0
    )

    consumer_throughput = (
        consumed / consumer_seconds
        if consumer_seconds > 0
        else 0
    )

    overall_throughput = (
        consumed / overall_seconds
        if overall_seconds > 0
        else 0
    )

    print("=== 10M Order mmap IPC Audit ===")
    print()
    print("Producer -> mmap SPSC Ring Buffer -> Consumer")
    print("Order transfer: fixed binary mmap data")
    print("Pickle used for order transfer: NO")
    print("Python processes: 2")
    print()
    print(f"Orders produced : {produced}")
    print(f"Orders consumed : {consumed}")
    print(f"First order ID  : {first_order_id}")
    print(f"Last order ID   : {last_order_id}")
    print(f"FIFO ordering   : {fifo_ok}")
    print()
    print(
        f"Producer throughput: "
        f"{producer_throughput:.2f} orders/second"
    )
    print(
        f"Consumer throughput: "
        f"{consumer_throughput:.2f} orders/second"
    )
    print(
        f"End-to-end throughput: "
        f"{overall_throughput:.2f} orders/second"
    )
    print(
        f"Total elapsed time: "
        f"{overall_seconds:.6f} seconds"
    )
    print()
    print("IPC audit completed successfully.")

    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)


if __name__ == "__main__":
    mp.freeze_support()
    main()
