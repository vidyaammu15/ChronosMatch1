import time

from engine.matching_engine import MatchingEngine
from ipc.mmap_ring_buffer import MMapRingBuffer


FILE_PATH = "chronosmatch_ring.bin"
CAPACITY = 8
EXPECTED_ORDERS = 5


def main():
    buffer = MMapRingBuffer(
        file_path=FILE_PATH,
        capacity=CAPACITY,
        create=False,
    )

    engine = MatchingEngine()

    consumed = 0
    total_trades = 0

    try:
        print("Matching consumer started.")

        while consumed < EXPECTED_ORDERS:
            if not buffer.is_empty():
                order = buffer.read()

                print(
                    f"Received: "
                    f"id={order.order_id}, "
                    f"side={order.side.name}, "
                    f"price={order.price}, "
                    f"quantity={order.quantity}"
                )

                trades = engine.process_order(order)

                for trade in trades:
                    total_trades += 1

                    print(
                        f"Trade: "
                        f"buy_id={trade.buy_order_id}, "
                        f"sell_id={trade.sell_order_id}, "
                        f"price={trade.price}, "
                        f"quantity={trade.quantity}"
                    )

                consumed += 1

            else:
                time.sleep(0.1)

        print("\nMatching consumer finished.")
        print(f"Orders consumed: {consumed}")
        print(f"Trades generated: {total_trades}")

    finally:
        buffer.close()


if __name__ == "__main__":
    main()