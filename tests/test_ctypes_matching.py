from core.types import Order, OrderSide
from core.ctypes_types import COrder, order_to_c, c_to_order


def test_matching_order_can_convert_to_c():
    order = Order(
        order_id=1,
        side=OrderSide.BUY,
        price=65000,
        quantity=10,
        timestamp=123456,
    )

    c_order = order_to_c(order)

    assert isinstance(c_order, COrder)
    assert c_order.order_id == 1
    assert c_order.side == int(OrderSide.BUY)
    assert c_order.price == 65000
    assert c_order.quantity == 10
    assert c_order.timestamp == 123456


def test_matching_order_c_round_trip():
    order = Order(
        order_id=1,
        side=OrderSide.SELL,
        price=65001,
        quantity=5,
        timestamp=123456,
    )

    c_order = order_to_c(order)
    restored = c_to_order(c_order)

    assert restored == order
