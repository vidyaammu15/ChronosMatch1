from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine


def create_order(order_id, side, price, quantity):
    return Order(
        order_id=order_id,
        side=side,
        price=price,
        quantity=quantity,
        timestamp=order_id,
    )


def test_buy_sell_match():
    engine = MatchingEngine()

    buy = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    sell = create_order(
        2,
        OrderSide.SELL,
        65000,
        5,
    )

    engine.process_order(buy)

    trades = engine.process_order(sell)

    assert len(trades) == 1
    assert trades[0].buy_order_id == 1
    assert trades[0].sell_order_id == 2
    assert trades[0].price == 65000
    assert trades[0].quantity == 5


def test_no_match_when_prices_do_not_cross():
    engine = MatchingEngine()

    buy = create_order(
        1,
        OrderSide.BUY,
        64900,
        10,
    )

    sell = create_order(
        2,
        OrderSide.SELL,
        65000,
        5,
    )

    engine.process_order(buy)

    trades = engine.process_order(sell)

    assert trades == []
    assert engine.book.best_bid() == 64900
    assert engine.book.best_ask() == 65000


def test_full_fill():
    engine = MatchingEngine()

    buy = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    sell = create_order(
        2,
        OrderSide.SELL,
        65000,
        10,
    )

    engine.process_order(buy)

    trades = engine.process_order(sell)

    assert len(trades) == 1
    assert trades[0].quantity == 10

    assert engine.book.best_bid() is None
    assert engine.book.best_ask() is None


def test_partial_fill():
    engine = MatchingEngine()

    buy = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    sell = create_order(
        2,
        OrderSide.SELL,
        65000,
        4,
    )

    engine.process_order(buy)

    trades = engine.process_order(sell)

    assert len(trades) == 1
    assert trades[0].quantity == 4

    assert engine.book.bid_quantity(65000) == 6
    assert engine.book.best_ask() is None


def test_multiple_matches():
    engine = MatchingEngine()

    buy1 = create_order(
        1,
        OrderSide.BUY,
        65000,
        5,
    )

    buy2 = create_order(
        2,
        OrderSide.BUY,
        65000,
        5,
    )

    sell = create_order(
        3,
        OrderSide.SELL,
        65000,
        8,
    )

    engine.process_order(buy1)
    engine.process_order(buy2)

    trades = engine.process_order(sell)

    assert len(trades) == 2

    assert trades[0].buy_order_id == 1
    assert trades[0].quantity == 5

    assert trades[1].buy_order_id == 2
    assert trades[1].quantity == 3

    assert engine.book.bid_quantity(65000) == 2


def test_price_priority_for_buy_orders():
    engine = MatchingEngine()

    low_price_buy = create_order(
        1,
        OrderSide.BUY,
        64900,
        10,
    )

    high_price_buy = create_order(
        2,
        OrderSide.BUY,
        65000,
        10,
    )

    sell = create_order(
        3,
        OrderSide.SELL,
        64900,
        10,
    )

    engine.process_order(low_price_buy)
    engine.process_order(high_price_buy)

    trades = engine.process_order(sell)

    assert len(trades) == 1

    # Highest bid should have priority.
    assert trades[0].buy_order_id == 2
    assert trades[0].quantity == 10

    assert engine.book.best_bid() == 64900


def test_time_priority_same_price():
    engine = MatchingEngine()

    first_buy = create_order(
        1,
        OrderSide.BUY,
        65000,
        5,
    )

    second_buy = create_order(
        2,
        OrderSide.BUY,
        65000,
        5,
    )

    sell = create_order(
        3,
        OrderSide.SELL,
        65000,
        6,
    )

    engine.process_order(first_buy)
    engine.process_order(second_buy)

    trades = engine.process_order(sell)

    assert len(trades) == 2

    # Earlier order gets filled first.
    assert trades[0].buy_order_id == 1
    assert trades[0].quantity == 5

    assert trades[1].buy_order_id == 2
    assert trades[1].quantity == 1


def test_price_priority_for_sell_orders():
    engine = MatchingEngine()

    high_price_sell = create_order(
        1,
        OrderSide.SELL,
        65100,
        10,
    )

    low_price_sell = create_order(
        2,
        OrderSide.SELL,
        65000,
        10,
    )

    buy = create_order(
        3,
        OrderSide.BUY,
        65100,
        10,
    )

    engine.process_order(high_price_sell)
    engine.process_order(low_price_sell)

    trades = engine.process_order(buy)

    assert len(trades) == 1

    # Lowest ask should have priority.
    assert trades[0].sell_order_id == 2
    assert trades[0].quantity == 10

    assert engine.book.best_ask() == 65100