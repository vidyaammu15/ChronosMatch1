import ctypes

from core.ctypes_types import (
    COrder,
    c_order_size,
    c_to_order,
    order_to_c,
)
from core.types import Order, OrderSide


def create_order():
    return Order(
        order_id=123,
        side=OrderSide.BUY,
        price=65000,
        quantity=10,
        timestamp=999999,
    )


def test_c_order_structure():
    order = create_order()

    c_order = order_to_c(order)

    assert isinstance(c_order, COrder)

    assert c_order.order_id == 123
    assert c_order.side == int(OrderSide.BUY)
    assert c_order.price == 65000
    assert c_order.quantity == 10
    assert c_order.timestamp == 999999


def test_c_order_round_trip():
    order = create_order()

    c_order = order_to_c(order)
    restored = c_to_order(c_order)

    assert restored.order_id == order.order_id
    assert restored.side == order.side
    assert restored.price == order.price
    assert restored.quantity == order.quantity
    assert restored.timestamp == order.timestamp


def test_c_order_size():
    assert c_order_size() == ctypes.sizeof(COrder)


def test_c_order_is_fixed_size():
    assert c_order_size() > 0