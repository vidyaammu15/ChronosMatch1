from core.types import Order, OrderSide
from engine.order_book import LimitOrderBook


def create_order(order_id, side, price, quantity):
    return Order(
        order_id=order_id,
        side=side,
        price=price,
        quantity=quantity,
        timestamp=order_id,
    )


def test_add_buy_order():
    book = LimitOrderBook()

    order = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    book.add_order(order)

    assert book.best_bid() == 65000
    assert book.bid_quantity(65000) == 10


def test_add_sell_order():
    book = LimitOrderBook()

    order = create_order(
        1,
        OrderSide.SELL,
        65005,
        5,
    )

    book.add_order(order)

    assert book.best_ask() == 65005
    assert book.ask_quantity(65005) == 5


def test_best_bid_is_highest_price():
    book = LimitOrderBook()

    book.add_order(
        create_order(1, OrderSide.BUY, 64999, 10)
    )

    book.add_order(
        create_order(2, OrderSide.BUY, 65002, 5)
    )

    book.add_order(
        create_order(3, OrderSide.BUY, 65001, 8)
    )

    assert book.best_bid() == 65002


def test_best_ask_is_lowest_price():
    book = LimitOrderBook()

    book.add_order(
        create_order(1, OrderSide.SELL, 65005, 10)
    )

    book.add_order(
        create_order(2, OrderSide.SELL, 65002, 5)
    )

    book.add_order(
        create_order(3, OrderSide.SELL, 65003, 8)
    )

    assert book.best_ask() == 65002


def test_multiple_orders_same_price():
    book = LimitOrderBook()

    order1 = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    order2 = create_order(
        2,
        OrderSide.BUY,
        65000,
        20,
    )

    book.add_order(order1)
    book.add_order(order2)

    assert book.bid_quantity(65000) == 30


def test_remove_order():
    book = LimitOrderBook()

    order = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    book.add_order(order)

    assert book.remove_order(order) is True
    assert book.best_bid() is None


def test_empty_book():
    book = LimitOrderBook()

    assert book.best_bid() is None
    assert book.best_ask() is None


def test_cancel_buy_order():
    book = LimitOrderBook()

    order = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    book.add_order(order)

    assert book.cancel_order(order) is True
    assert book.best_bid() is None


def test_cancel_sell_order():
    book = LimitOrderBook()

    order = create_order(
        1,
        OrderSide.SELL,
        65000,
        10,
    )

    book.add_order(order)

    assert book.cancel_order(order) is True
    assert book.best_ask() is None


def test_cancel_nonexistent_order():
    book = LimitOrderBook()

    order = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    assert book.cancel_order(order) is False


def test_cancel_one_of_multiple_orders():
    book = LimitOrderBook()

    order1 = create_order(
        1,
        OrderSide.BUY,
        65000,
        10,
    )

    order2 = create_order(
        2,
        OrderSide.BUY,
        65000,
        20,
    )

    book.add_order(order1)
    book.add_order(order2)

    assert book.cancel_order(order1) is True
    assert book.best_bid() == 65000
    assert book.bid_quantity(65000) == 20