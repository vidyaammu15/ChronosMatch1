import asyncio

from core.types import OrderSide
from simulator.market_firehose import MarketFirehose


def test_generate_order():
    firehose = MarketFirehose()

    order = firehose.generate_order()

    assert order.order_id == 1
    assert order.side == OrderSide.BUY
    assert order.price == 65001
    assert order.quantity == 2


def test_generate_multiple_orders():
    firehose = MarketFirehose()

    orders = [
        firehose.generate_order()
        for _ in range(10)
    ]

    assert len(orders) == 10
    assert orders[0].order_id == 1
    assert orders[-1].order_id == 10


def test_async_stream():
    async def collect_orders():
        firehose = MarketFirehose()

        orders = []

        async for order in firehose.stream(100):
            orders.append(order)

        return orders

    orders = asyncio.run(collect_orders())

    assert len(orders) == 100
    assert orders[0].order_id == 1
    assert orders[-1].order_id == 100