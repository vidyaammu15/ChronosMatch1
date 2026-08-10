import mmap
import os

from core.serializer import order_size
from core.types import Order


class SharedMemoryBuffer:
    def __init__(
        self,
        file_path: str,
        capacity: int,
        create: bool = True,
    ):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than zero")

        self.file_path = file_path
        self.capacity = capacity
        self.slot_size = order_size()
        self.size = self.capacity * self.slot_size

        if create:
            self._file = open(self.file_path, "w+b")
            self._file.truncate(self.size)
        else:
            self._file = open(self.file_path, "r+b")

        self._mmap = mmap.mmap(
            self._file.fileno(),
            self.size,
        )

    def write(self, index: int, data: bytes) -> None:
        if not 0 <= index < self.capacity:
            raise IndexError("Invalid buffer index")

        if len(data) != self.slot_size:
            raise ValueError(
                f"Expected {self.slot_size} bytes, "
                f"received {len(data)} bytes"
            )

        offset = index * self.slot_size

        self._mmap.seek(offset)
        self._mmap.write(data)

        self._mmap.flush()

    def read(self, index: int) -> bytes:
        if not 0 <= index < self.capacity:
            raise IndexError("Invalid buffer index")

        offset = index * self.slot_size

        self._mmap.seek(offset)
        return self._mmap.read(self.slot_size)

    def close(self) -> None:
        self._mmap.close()
        self._file.close()

    def unlink(self) -> None:
        """
        Remove the backing file after closing the mmap.
        """
        if os.path.exists(self.file_path):
            os.remove(self.file_path)