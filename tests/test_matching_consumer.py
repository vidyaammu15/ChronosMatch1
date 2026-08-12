from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine


def test_mmap_orders_can_be_processed_by_matching_engine():
    engine = MatchingEngine()

    buy = Order(
        order_id=1,
        side=OrderSide.BUY,
        price=65000,
        quantity=10,
        timestamp=1,
    )

    sell = Order(
        order_id=2,
        side=OrderSide.SELL,
        price=65000,
        quantity=5,
        timestamp=2,
    )

    engine.process_order(buy)

    trades = engine.process_order(sell)

    assert len(trades) == 1
    assert trades[0].buy_order_id == 1
    assert trades[0].sell_order_id == 2
    assert trades[0].price == 65000
    assert trades[0].quantity == 5


def test_mmap_matching_partial_fill():
    engine = MatchingEngine()

    buy = Order(
        order_id=1,
        side=OrderSide.BUY,
        price=65000,
        quantity=10,
        timestamp=1,
    )

    sell = Order(
        order_id=2,
        side=OrderSide.SELL,
        price=65000,
        quantity=4,
        timestamp=2,
    )

    engine.process_order(buy)

    trades = engine.process_order(sell)

    assert len(trades) == 1
    assert trades[0].quantity == 4
    assert engine.book.bid_quantity(65000) == 6