import mmap
import os
import struct

from core.serializer import serialize_order, deserialize_order, order_size
from core.types import Order


# Header:
# Q = head
# Q = tail
# Q = count
HEADER_FORMAT = "=QQQ"
HEADER_STRUCT = struct.Struct(HEADER_FORMAT)

HEADER_SIZE = HEADER_STRUCT.size


class MMapRingBuffer:
    """
    Ring buffer stored inside an mmap-backed file.

    Layout:

    ┌──────────────────────────────────────────┐
    │ Header                                   │
    │ head | tail | count                      │
    ├──────────────────────────────────────────┤
    │ Slot 0                                   │
    ├──────────────────────────────────────────┤
    │ Slot 1                                   │
    ├──────────────────────────────────────────┤
    │ Slot 2                                   │
    ├──────────────────────────────────────────┤
    │ ...                                      │
    └──────────────────────────────────────────┘
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
            HEADER_SIZE +
            self.capacity * self.slot_size
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
            self._write_header(
                head=0,
                tail=0,
                count=0,
            )

    def _read_header(self):
        self._mmap.seek(0)

        data = self._mmap.read(HEADER_SIZE)

        return HEADER_STRUCT.unpack(data)

    def _write_header(
        self,
        head: int,
        tail: int,
        count: int,
    ):
        self._mmap.seek(0)

        data = HEADER_STRUCT.pack(
            head,
            tail,
            count,
        )

        self._mmap.write(data)
        self._mmap.flush()

    @property
    def head(self):
        return self._read_header()[0]

    @property
    def tail(self):
        return self._read_header()[1]

    @property
    def count(self):
        return self._read_header()[2]

    def is_empty(self) -> bool:
        return self.count == 0

    def is_full(self) -> bool:
        return self.count == self.capacity

    def size(self) -> int:
        return self.count

    def _slot_offset(self, index: int) -> int:
        if not 0 <= index < self.capacity:
            raise IndexError("Invalid ring-buffer index")

        return HEADER_SIZE + index * self.slot_size

    def write(self, order: Order) -> None:
        if self.is_full():
            raise BufferError("Ring buffer is full")

        head, tail, count = self._read_header()

        data = serialize_order(order)

        offset = self._slot_offset(head)

        self._mmap.seek(offset)
        self._mmap.write(data)

        head = (head + 1) % self.capacity
        count += 1

        self._write_header(
            head=head,
            tail=tail,
            count=count,
        )

    def read(self) -> Order:
        if self.is_empty():
            raise BufferError("Ring buffer is empty")

        head, tail, count = self._read_header()

        offset = self._slot_offset(tail)

        self._mmap.seek(offset)

        data = self._mmap.read(self.slot_size)

        order = deserialize_order(data)

        tail = (tail + 1) % self.capacity
        count -= 1

        self._write_header(
            head=head,
            tail=tail,
            count=count,
        )

        return order

    def close(self):
        self._mmap.close()
        self._file.close()

    def unlink(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)