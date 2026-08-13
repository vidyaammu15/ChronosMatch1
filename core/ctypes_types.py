import ctypes

from core.types import Order, OrderSide


class COrder(ctypes.Structure):
    """
    C-compatible representation of an Order.

    Field layout:
        order_id  : unsigned long long
        side      : unsigned char
        price     : unsigned long long
        quantity  : unsigned long long
        timestamp : unsigned long long
    """

    _fields_ = [
        ("order_id", ctypes.c_uint64),
        ("side", ctypes.c_uint8),
        ("price", ctypes.c_uint64),
        ("quantity", ctypes.c_uint64),
        ("timestamp", ctypes.c_uint64),
    ]


def order_to_c(order: Order) -> COrder:
    """Convert a Python Order into a C-compatible structure."""

    return COrder(
        order_id=order.order_id,
        side=int(order.side),
        price=order.price,
        quantity=order.quantity,
        timestamp=order.timestamp,
    )


def c_to_order(order: COrder) -> Order:
    """Convert a C-compatible structure back into a Python Order."""

    return Order(
        order_id=order.order_id,
        side=OrderSide(order.side),
        price=order.price,
        quantity=order.quantity,
        timestamp=order.timestamp,
    )


def c_order_size() -> int:
    """Return the size of the C-compatible order structure."""

    return ctypes.sizeof(COrder)