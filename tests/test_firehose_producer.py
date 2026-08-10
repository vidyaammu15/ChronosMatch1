import asyncio

from ipc.mmap_ring_buffer import MMapRingBuffer
from simulator.market_firehose import MarketFirehose


def test_firehose_to_mmap(tmp_path):
    file_path = str(tmp_path / "firehose.bin")

    capacity = 32
    order_count = 20

    buffer = MMapRingBuffer(
        file_path=file_path,
        capacity=capacity,
        create=True,
    )

    async def produce():
        firehose = MarketFirehose()

        async for order in firehose.stream(order_count):
            buffer.write(order)

    try:
        asyncio.run(produce())

        assert buffer.size() == order_count

        orders = []

        while not buffer.is_empty():
            orders.append(buffer.read())

        assert len(orders) == order_count

        assert orders[0].order_id == 1
        assert orders[-1].order_id == order_count

    finally:
        buffer.close()