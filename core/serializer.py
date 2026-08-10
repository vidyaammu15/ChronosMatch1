import struct

from core.types import Order, OrderSide
from core.constants import ORDER_FORMAT


ORDER_STRUCT = struct.Struct(ORDER_FORMAT)


def serialize_order(order: Order) -> bytes:
    """Convert an Order object into fixed-size binary data."""

    return ORDER_STRUCT.pack(
        order.order_id,
        int(order.side),
        order.price,
        order.quantity,
        order.timestamp,
    )


def deserialize_order(data: bytes) -> Order:
    """Convert fixed-size binary data back into an Order object."""

    order_id, side, price, quantity, timestamp = ORDER_STRUCT.unpack(data)

    return Order(
        order_id=order_id,
        side=OrderSide(side),
        price=price,
        quantity=quantity,
        timestamp=timestamp,
    )


def order_size() -> int:
    """Return the number of bytes required for one serialized order."""

    return ORDER_STRUCT.size