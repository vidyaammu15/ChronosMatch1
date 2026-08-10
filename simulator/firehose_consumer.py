import time

from ipc.mmap_ring_buffer import MMapRingBuffer


FILE_PATH = "chronosmatch_firehose.bin"
CAPACITY = 2048
EXPECTED_ORDERS = 1000


def main():
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    consumed = 0
    start = time.perf_counter()

    try:
        print("Consumer started.")

        while consumed < EXPECTED_ORDERS:
            if not buffer.is_empty():
                order = buffer.read()
                consumed += 1

                if consumed <= 10 or consumed % 100 == 0:
                    print(
                        f"Consumed #{consumed}: "
                        f"id={order.order_id}, "
                        f"side={order.side.name}, "
                        f"price={order.price}, "
                        f"quantity={order.quantity}"
                    )
            else:
                time.sleep(0.0001)

        elapsed = time.perf_counter() - start

        throughput = (
            consumed / elapsed
            if elapsed > 0
            else 0
        )

        print("\nConsumer finished.")
        print(f"Orders consumed: {consumed}")
        print(f"Elapsed time: {elapsed:.6f} seconds")
        print(f"Throughput: {throughput:.2f} orders/second")

    finally:
        buffer.close()


if __name__ == "__main__":
    main()