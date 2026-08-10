from core.types import Order, OrderSide


def test_order_creation():
    order = Order(
        order_id=1,
        side=OrderSide.BUY,
        price=65200,
        quantity=5,
        timestamp=123456789
    )

    assert order.order_id == 1
    assert order.side == OrderSide.BUY
    assert order.price == 65200
    assert order.quantity == 5