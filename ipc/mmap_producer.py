import time

from core.types import Order, OrderSide
from ipc.mmap_ring_buffer import MMapRingBuffer


FILE_PATH = "chronosmatch_ring.bin"
CAPACITY = 8


def main():
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )

    try:
        print("Producer started.")

        for order_id in range(1, 6):
            order = Order(
                order_id=order_id,
                side=OrderSide.BUY if order_id % 2 else OrderSide.SELL,
                price=65000 + order_id,
                quantity=10 + order_id,
                timestamp=time.perf_counter_ns(),
            )

            buffer.write(order)

            print(
                f"Produced: "
                f"id={order.order_id}, "
                f"side={order.side.name}, "
                f"price={order.price}, "
                f"quantity={order.quantity}"
            )

            time.sleep(1)

        print("\nAll orders produced.")
        input("Press Enter to stop producer...")

    finally:
        buffer.close()


if __name__ == "__main__":
    main()