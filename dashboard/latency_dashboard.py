import curses
import time

from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine


def create_demo_orders(engine):
    for order_id in range(1, 101):
        if order_id % 2 == 1:
            order = Order(
                order_id=order_id,
                side=OrderSide.BUY,
                price=65000 - (order_id % 5),
                quantity=(order_id % 10) + 1,
                timestamp=time.perf_counter_ns(),
            )
        else:
            order = Order(
                order_id=order_id,
                side=OrderSide.SELL,
                price=65000 + (order_id % 5),
                quantity=(order_id % 10) + 1,
                timestamp=time.perf_counter_ns(),
            )

        engine.process_order(order)


def draw_dashboard(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    engine = MatchingEngine()
    create_demo_orders(engine)

    while True:
        start = time.perf_counter_ns()

        stdscr.erase()

        height, width = stdscr.getmaxyx()

        title = "CHRONOSMATCH - LATENCY DASHBOARD"

        try:
            stdscr.addstr(
                0,
                max(0, (width - len(title)) // 2),
                title,
                curses.A_BOLD,
            )

            stdscr.addstr(2, 2, "ORDER BOOK", curses.A_BOLD)

            book = engine.book

            stdscr.addstr(4, 4, "ASK", curses.A_BOLD)

            ask_prices = sorted(book.asks.keys())
            row = 5

            for price in ask_prices[:5]:
                quantity = book.ask_quantity(price)

                if row < height:
                    stdscr.addstr(
                        row,
                        4,
                        f"{price:<10} {quantity:>8}",
                    )

                row += 1

            best_ask = book.best_ask()

            if row < height:
                stdscr.addstr(row, 4, "-" * 25)

            row += 2

            if row < height:
                stdscr.addstr(row, 4, "BID", curses.A_BOLD)

            row += 1

            bid_prices = sorted(
                book.bids.keys(),
                reverse=True,
            )

            for price in bid_prices[:5]:
                quantity = book.bid_quantity(price)

                if row < height:
                    stdscr.addstr(
                        row,
                        4,
                        f"{price:<10} {quantity:>8}",
                    )

                row += 1

            best_bid = book.best_bid()

            if best_bid is not None and best_ask is not None:
                spread = best_ask - best_bid
            else:
                spread = None

            latency_us = (
                time.perf_counter_ns() - start
            ) / 1000

            stats_row = min(row + 2, height - 6)

            if stats_row >= 0:
                stdscr.addstr(
                    stats_row,
                    2,
                    f"Best Bid   : {best_bid}",
                )

                stdscr.addstr(
                    stats_row + 1,
                    2,
                    f"Best Ask   : {best_ask}",
                )

                stdscr.addstr(
                    stats_row + 2,
                    2,
                    f"Spread     : {spread}",
                )

                stdscr.addstr(
                    stats_row + 3,
                    2,
                    f"UI Latency : {latency_us:.3f} us",
                )

            footer = "Press Q to quit"

            stdscr.addstr(
                height - 1,
                max(0, width - len(footer) - 2),
                footer,
            )

        except curses.error:
            pass

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            break

        time.sleep(0.05)


def main():
    curses.wrapper(draw_dashboard)


if __name__ == "__main__":
    main()
