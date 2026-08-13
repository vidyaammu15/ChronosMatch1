import curses
import time

from core.ctypes_types import order_to_c
from engine.matching_engine import MatchingEngine
from simulator.market_firehose import MarketFirehose


REFRESH_SECONDS = 0.05
ORDERS_PER_REFRESH = 10


def draw_dashboard(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    firehose = MarketFirehose()
    engine = MatchingEngine()

    total_orders = 0
    total_trades = 0

    while True:
        frame_start = time.perf_counter_ns()

        # Process a small batch on every dashboard refresh.
        for _ in range(ORDERS_PER_REFRESH):
            order = firehose.generate_order()

            # Use the C-compatible representation at the
            # matching-engine boundary.
            c_order = order_to_c(order)

            trades = engine.process_c_order(c_order)

            total_orders += 1
            total_trades += len(trades)

        stdscr.erase()

        height, width = stdscr.getmaxyx()

        title = "CHRONOSMATCH - LIVE LATENCY DASHBOARD"

        try:
            stdscr.addstr(
                0,
                max(0, (width - len(title)) // 2),
                title,
                curses.A_BOLD,
            )

            stdscr.addstr(
                2,
                2,
                "LIVE ORDER BOOK",
                curses.A_BOLD,
            )

            book = engine.book

            # -------------------------
            # ASK SIDE
            # -------------------------

            stdscr.addstr(
                4,
                4,
                "ASK",
                curses.A_BOLD,
            )

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

            # -------------------------
            # SPREAD
            # -------------------------

            if row < height:
                stdscr.addstr(
                    row,
                    4,
                    "-" * 25,
                )

            row += 2

            if row < height:
                stdscr.addstr(
                    row,
                    4,
                    "BID",
                    curses.A_BOLD,
                )

            row += 1

            # -------------------------
            # BID SIDE
            # -------------------------

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

            if (
                best_bid is not None
                and best_ask is not None
            ):
                spread = best_ask - best_bid
            else:
                spread = None

            frame_latency_us = (
                time.perf_counter_ns() - frame_start
            ) / 1000

            stats_row = min(
                row + 2,
                max(5, height - 8),
            )

            if stats_row < height:
                stdscr.addstr(
                    stats_row,
                    2,
                    f"Best Bid       : {best_bid}",
                )

            if stats_row + 1 < height:
                stdscr.addstr(
                    stats_row + 1,
                    2,
                    f"Best Ask       : {best_ask}",
                )

            if stats_row + 2 < height:
                stdscr.addstr(
                    stats_row + 2,
                    2,
                    f"Spread         : {spread}",
                )

            if stats_row + 3 < height:
                stdscr.addstr(
                    stats_row + 3,
                    2,
                    f"Orders Processed: {total_orders}",
                )

            if stats_row + 4 < height:
                stdscr.addstr(
                    stats_row + 4,
                    2,
                    f"Trades Generated: {total_trades}",
                )

            if stats_row + 5 < height:
                stdscr.addstr(
                    stats_row + 5,
                    2,
                    f"Frame Latency  : {frame_latency_us:.3f} us",
                )

            footer = "Q = Quit"

            if height > 0:
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

        time.sleep(REFRESH_SECONDS)


def main():
    curses.wrapper(draw_dashboard)


if __name__ == "__main__":
    main()
