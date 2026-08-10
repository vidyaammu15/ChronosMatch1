from core.serializer import (
    serialize_order,
    deserialize_order,
    order_size,
)
from core.types import Order


class RingBuffer:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than zero")

        self.capacity = capacity
        self._buffer = bytearray(capacity * order_size())

        self.head = 0
        self.tail = 0
        self.count = 0

    def is_empty(self) -> bool:
        return self.count == 0

    def is_full(self) -> bool:
        return self.count == self.capacity

    def size(self) -> int:
        return self.count

    def write(self, order: Order) -> None:
        if self.is_full():
            raise BufferError("Ring buffer is full")

        data = serialize_order(order)

        start = self.head * order_size()
        end = start + order_size()

        self._buffer[start:end] = data

        self.head = (self.head + 1) % self.capacity
        self.count += 1

    def read(self) -> Order:
        if self.is_empty():
            raise BufferError("Ring buffer is empty")

        start = self.tail * order_size()
        end = start + order_size()

        data = bytes(self._buffer[start:end])

        order = deserialize_order(data)

        self.tail = (self.tail + 1) % self.capacity
        self.count -= 1

        return order