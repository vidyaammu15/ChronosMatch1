from core.types import Order, OrderSide
from core.serializer import (
    serialize_order,
    deserialize_order,
    order_size,
)


def test_order_serialization():
    original = Order(
        order_id=1001,
        side=OrderSide.BUY,
        price=65200,
        quantity=5,
        timestamp=123456789,
    )

    data = serialize_order(original)

    assert isinstance(data, bytes)
    assert len(data) == order_size()

    restored = deserialize_order(data)

    assert restored.order_id == original.order_id
    assert restored.side == original.side
    assert restored.price == original.price
    assert restored.quantity == original.quantity
    assert restored.timestamp == original.timestamp