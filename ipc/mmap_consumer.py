import time

from ipc.mmap_ring_buffer import MMapRingBuffer


FILE_PATH = "chronosmatch_ring.bin"
CAPACITY = 8
EXPECTED_ORDERS = 5


def main():
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    consumed = 0

    try:
        print("Consumer started.")

        while consumed < EXPECTED_ORDERS:
            if not buffer.is_empty():
                order = buffer.read()

                print(
                    f"Consumed: "
                    f"id={order.order_id}, "
                    f"side={order.side.name}, "
                    f"price={order.price}, "
                    f"quantity={order.quantity}"
                )

                consumed += 1
            else:
                time.sleep(0.1)

        print("\nConsumer finished.")

    finally:
        buffer.close()


if __name__ == "__main__":
    main()