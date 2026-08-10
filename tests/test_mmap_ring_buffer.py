from core.types import Order, OrderSide
from ipc.mmap_ring_buffer import MMapRingBuffer


def create_order(order_id: int) -> Order:
    return Order(
        order_id=order_id,
        side=OrderSide.BUY,
        price=65000 + order_id,
        quantity=10,
        timestamp=1000000 + order_id,
    )


def test_mmap_ring_buffer_write_read(tmp_path):
    file_path = str(tmp_path / "ring_buffer.bin")

    buffer = MMapRingBuffer(
        file_path=file_path,
        capacity=4,
    )

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

    assert buffer.is_empty()

    buffer.close()


def test_mmap_ring_buffer_full(tmp_path):
    file_path = str(tmp_path / "ring_buffer.bin")

    buffer = MMapRingBuffer(
        file_path=file_path,
        capacity=2,
    )

    buffer.write(create_order(1))
    buffer.write(create_order(2))

    assert buffer.is_full()

    try:
        buffer.write(create_order(3))
        assert False, "Expected BufferError"
    except BufferError:
        pass

    buffer.close()


def test_mmap_ring_buffer_wraparound(tmp_path):
    file_path = str(tmp_path / "ring_buffer.bin")

    buffer = MMapRingBuffer(
        file_path=file_path,
        capacity=2,
    )

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

    buffer.close()