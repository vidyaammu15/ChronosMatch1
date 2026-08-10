from core.serializer import deserialize_order
from ipc.shared_memory import SharedMemoryBuffer


FILE_PATH = "chronosmatch_shared_memory.bin"
CAPACITY = 16


def main():
    memory = SharedMemoryBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    try:
        data = memory.read(0)

        order = deserialize_order(data)

        print("Consumer read order:")
        print(order)

    finally:
        memory.close()


if __name__ == "__main__":
    main()