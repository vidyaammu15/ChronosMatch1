import time

from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine


def create_order(order_id, side, price, quantity):
    return Order(
        order_id=order_id,
        side=side,
        price=price,
        quantity=quantity,
        timestamp=time.perf_counter_ns(),
    )


def main():
    engine = MatchingEngine()

    buy = create_order(
        order_id=1,
        side=OrderSide.BUY,
        price=65000,
        quantity=10,
    )

    sell = create_order(
        order_id=2,
        side=OrderSide.SELL,
        price=65000,
        quantity=10,
    )

    start = time.perf_counter_ns()

    # First place the BUY order.
    buy_trades = engine.process_order(buy)

    # Then place the matching SELL order.
    sell_trades = engine.process_order(sell)

    elapsed_ns = time.perf_counter_ns() - start

    print("=== Matching Engine Verification ===")
    print()
    print("BUY:")
    print(f"  Order ID : {buy.order_id}")
    print(f"  Price    : {buy.price}")
    print(f"  Quantity : {buy.quantity}")

    print()
    print("SELL:")
    print(f"  Order ID : {sell.order_id}")
    print(f"  Price    : {sell.price}")
    print(f"  Quantity : {sell.quantity}")

    print()
    print(f"Trades generated: {len(sell_trades)}")

    if sell_trades:
        trade = sell_trades[0]

        print()
        print("TRADE:")
        print(f"  Buy Order  : {trade.buy_order_id}")
        print(f"  Sell Order : {trade.sell_order_id}")
        print(f"  Price      : {trade.price}")
        print(f"  Quantity   : {trade.quantity}")

    print()
    print(f"Matching latency: {elapsed_ns / 1000:.3f} microseconds")

    assert buy_trades == []
    assert len(sell_trades) == 1

    trade = sell_trades[0]

    assert trade.buy_order_id == 1
    assert trade.sell_order_id == 2
    assert trade.price == 65000
    assert trade.quantity == 10

    assert engine.book.best_bid() is None
    assert engine.book.best_ask() is None

    print()
    print("VERIFICATION PASSED")
    print("BUY and SELL orders matched successfully.")


if __name__ == "__main__":
    main()
