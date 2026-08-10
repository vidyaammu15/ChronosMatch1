import time

from core.serializer import serialize_order
from core.types import Order, OrderSide
from ipc.shared_memory import SharedMemoryBuffer


FILE_PATH = "chronosmatch_shared_memory.bin"
CAPACITY = 16


def main():
    memory = SharedMemoryBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=True,
    )

    try:
        order = Order(
            order_id=1001,
            side=OrderSide.BUY,
            price=65200,
            quantity=5,
            timestamp=time.perf_counter_ns(),
        )

        data = serialize_order(order)

        memory.write(0, data)

        print("Producer wrote order:")
        print(order)

        print("\nShared memory file:")
        print(FILE_PATH)

        # Keep the mapping alive so another process can open it.
        input("\nPress Enter to stop producer...")

    finally:
        memory.close()


if __name__ == "__main__":
    main()