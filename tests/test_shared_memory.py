from core.serializer import serialize_order, deserialize_order
from core.types import Order, OrderSide
from ipc.shared_memory import SharedMemoryBuffer


def test_shared_memory_write_and_read(tmp_path):
    file_path = str(tmp_path / "chronosmatch_shm.bin")

    memory = SharedMemoryBuffer(
        file_path=file_path,
        capacity=4,
    )

    order = Order(
        order_id=1001,
        side=OrderSide.BUY,
        price=65200,
        quantity=5,
        timestamp=123456789,
    )

    data = serialize_order(order)

    memory.write(0, data)

    raw_data = memory.read(0)

    restored = deserialize_order(raw_data)

    assert restored.order_id == order.order_id
    assert restored.side == order.side
    assert restored.price == order.price
    assert restored.quantity == order.quantity
    assert restored.timestamp == order.timestamp

    memory.close()