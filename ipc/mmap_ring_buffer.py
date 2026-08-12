import mmap
import os
import struct

from core.serializer import serialize_order, deserialize_order, order_size
from core.types import Order


# Header layout:
#
# 0 - 7   : head
# 8 - 15  : tail
#
# Producer owns head.
# Consumer owns tail.

HEAD_OFFSET = 0
TAIL_OFFSET = 8

HEADER_FORMAT = "=QQ"
HEADER_STRUCT = struct.Struct(HEADER_FORMAT)
HEADER_SIZE = HEADER_STRUCT.size


class MMapRingBuffer:
    """
    Single-producer / single-consumer mmap ring buffer.

    Producer:
        - reads head and tail
        - writes order data
        - updates ONLY head

    Consumer:
        - reads head and tail
        - reads order data
        - updates ONLY tail

    This avoids both processes overwriting each other's
    header updates.
    """

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

        self.total_size = (
            HEADER_SIZE
            + self.capacity * self.slot_size
        )

        if create:
            self._file = open(self.file_path, "w+b")
            self._file.truncate(self.total_size)
        else:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(self.file_path)

            self._file = open(self.file_path, "r+b")

        self._mmap = mmap.mmap(
            self._file.fileno(),
            self.total_size,
        )

        if create:
            self._write_head(0)
            self._write_tail(0)
            self._mmap.flush()

    # -----------------------------
    # Header operations
    # -----------------------------

    def _read_head(self) -> int:
        self._mmap.seek(HEAD_OFFSET)

        data = self._mmap.read(8)

        return struct.unpack("=Q", data)[0]

    def _read_tail(self) -> int:
        self._mmap.seek(TAIL_OFFSET)

        data = self._mmap.read(8)

        return struct.unpack("=Q", data)[0]

    def _write_head(self, head: int) -> None:
        self._mmap.seek(HEAD_OFFSET)

        self._mmap.write(
            struct.pack("=Q", head)
        )

    def _write_tail(self, tail: int) -> None:
        self._mmap.seek(TAIL_OFFSET)

        self._mmap.write(
            struct.pack("=Q", tail)
        )

    @property
    def head(self) -> int:
        return self._read_head()

    @property
    def tail(self) -> int:
        return self._read_tail()

    @property
    def count(self) -> int:
        return self.head - self.tail

    # -----------------------------
    # State
    # -----------------------------

    def is_empty(self) -> bool:
        return self.head == self.tail

    def is_full(self) -> bool:
        return (self.head - self.tail) >= self.capacity

    def size(self) -> int:
        return self.head - self.tail

    # -----------------------------
    # Slot
    # -----------------------------

    def _slot_offset(self, index: int) -> int:
        if not 0 <= index < self.capacity:
            raise IndexError("Invalid ring-buffer index")

        return (
            HEADER_SIZE
            + index * self.slot_size
        )

    # -----------------------------
    # Producer
    # -----------------------------

    def write(self, order: Order) -> None:
        head = self._read_head()
        tail = self._read_tail()

        if (head - tail) >= self.capacity:
            raise BufferError("Ring buffer is full")

        data = serialize_order(order)

        index = head % self.capacity
        offset = self._slot_offset(index)

        # Write the order first.
        self._mmap.seek(offset)
        self._mmap.write(data)

        # Publish the slot by advancing head.
        self._write_head(head + 1)

    # -----------------------------
    # Consumer
    # -----------------------------

    def read(self) -> Order:
        head = self._read_head()
        tail = self._read_tail()

        if head == tail:
            raise BufferError("Ring buffer is empty")

        index = tail % self.capacity
        offset = self._slot_offset(index)

        self._mmap.seek(offset)

        data = self._mmap.read(self.slot_size)

        order = deserialize_order(data)

        # Release the slot by advancing tail.
        self._write_tail(tail + 1)

        return order

    # -----------------------------
    # Cleanup
    # -----------------------------

    def close(self):
        self._mmap.flush()
        self._mmap.close()
        self._file.close()

    def unlink(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)