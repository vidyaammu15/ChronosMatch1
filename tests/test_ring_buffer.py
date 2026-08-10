import pytest

from core.types import Order, OrderSide
from ipc.ring_buffer import RingBuffer


def create_order(order_id: int) -> Order:
    return Order(
        order_id=order_id,
        side=OrderSide.BUY,
        price=65000 + order_id,
        quantity=10,
        timestamp=1000000 + order_id,
    )


def test_ring_buffer_write_and_read():
    buffer = RingBuffer(capacity=4)

    order = create_order(1)

    buffer.write(order)

    assert buffer.size() == 1
    assert not buffer.is_empty()

    result = buffer.read()

    assert result.order_id == order.order_id
    assert result.side == order.side
    assert result.price == order.price
    assert result.quantity == order.quantity
    assert result.timestamp == order.timestamp

    assert buffer.size() == 0
    assert buffer.is_empty()


def test_ring_buffer_full():
    buffer = RingBuffer(capacity=2)

    buffer.write(create_order(1))
    buffer.write(create_order(2))

    assert buffer.is_full()

    with pytest.raises(BufferError):
        buffer.write(create_order(3))


def test_ring_buffer_empty():
    buffer = RingBuffer(capacity=2)

    assert buffer.is_empty()

    with pytest.raises(BufferError):
        buffer.read()


def test_ring_buffer_wraparound():
    buffer = RingBuffer(capacity=2)

    buffer.write(create_order(1))
    buffer.write(create_order(2))

    first = buffer.read()

    assert first.order_id == 1

    buffer.write(create_order(3))

    second = buffer.read()
    third = buffer.read()

    assert second.order_id == 2
    assert third.order_id == 3

    assert buffer.is_empty()