import curses
import time

from core.ctypes_types import order_to_c
from core.types import Order, OrderSide
from engine.matching_engine import MatchingEngine
from simulator.market_firehose import MarketFirehose


REFRESH_SECONDS = 0.05
ORDERS_PER_REFRESH = 10
WHALE_LEVELS = 2


def create_whale_demo(engine):
    """
    Execute a real BUY order that clears multiple SELL price levels.
    The returned trades are used to calculate the Whale event.
    """

    sell_prices = [64990, 64991, 64992, 64993]

    for index, price in enumerate(sell_prices, start=1):
        engine.process_order(
            Order(
                order_id=9000 + index,
                side=OrderSide.SELL,
                price=price,
                quantity=5,
                timestamp=time.perf_counter_ns(),
            )
        )

    whale_order = Order(
        order_id=10000,
        side=OrderSide.BUY,
        price=64993,
        quantity=20,
        timestamp=time.perf_counter_ns(),
    )

    trades = engine.process_order(whale_order)

    return whale_order, trades


def draw_dashboard(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    firehose = MarketFirehose()
    engine = MatchingEngine()

    total_orders = 0
    total_trades = 0

    whale_order_id = None
    whale_levels = 0
    whale_quantity = 0
    whale_side = None

    whale_demo_done = False

    while True:
        frame_start = time.perf_counter_ns()

        # -------------------------------------------------
        # Controlled Whale demonstration.
        # Run before normal firehose orders so the demo
        # order book starts empty.
        # -------------------------------------------------

        if not whale_demo_done:
            whale_order, whale_trades = create_whale_demo(engine)

            trade_prices = set(
                trade.price
                for trade in whale_trades
            )

            levels_cleared = len(trade_prices)

            if levels_cleared >= WHALE_LEVELS:
                whale_order_id = whale_order.order_id
                whale_levels = levels_cleared
                whale_quantity = whale_order.quantity
                whale_side = whale_order.side

            total_trades += len(whale_trades)

            whale_demo_done = True

        # -------------------------------------------------
        # Normal market-firehose processing
        # -------------------------------------------------

        for _ in range(ORDERS_PER_REFRESH):
            order = firehose.generate_order()

            c_order = order_to_c(order)

            trades = engine.process_c_order(c_order)

            total_orders += 1
            total_trades += len(trades)

            if trades:
                trade_prices = set(
                    trade.price
                    for trade in trades
                )

                levels_cleared = len(trade_prices)

                if levels_cleared >= WHALE_LEVELS:
                    whale_order_id = order.order_id
                    whale_levels = levels_cleared
                    whale_quantity = order.quantity
                    whale_side = order.side

        # -------------------------------------------------
        # Dashboard
        # -------------------------------------------------

        stdscr.erase()

        height, width = stdscr.getmaxyx()

        title = "CHRONOSMATCH - LIVE LATENCY DASHBOARD"

        try:
            # -------------------------------------------------
            # Title
            # -------------------------------------------------

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

            # -------------------------------------------------
            # ASK
            # -------------------------------------------------

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

            # -------------------------------------------------
            # Separator
            # -------------------------------------------------

            if row < height:
                stdscr.addstr(
                    row,
                    4,
                    "-" * 25,
                )

            row += 2

            # -------------------------------------------------
            # BID
            # -------------------------------------------------

            if row < height:
                stdscr.addstr(
                    row,
                    4,
                    "BID",
                    curses.A_BOLD,
                )

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

            # -------------------------------------------------
            # Spread
            # -------------------------------------------------

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

            # -------------------------------------------------
            # Fixed Whale Alert section
            # -------------------------------------------------

            whale_row = 20

            if (
                whale_order_id is not None
                and whale_row < height
            ):
                alert = (
                    "WHALE ORDER DETECTED"
                )

                stdscr.addstr(
                    whale_row,
                    2,
                    alert[:max(1, width - 4)],
                    curses.A_BOLD | curses.A_REVERSE,
                )

                if whale_row + 1 < height:
                    stdscr.addstr(
                        whale_row + 1,
                        2,
                        (
                            f"Order ID       : {whale_order_id}"
                        )[:max(1, width - 4)],
                    )

                if whale_row + 2 < height:
                    stdscr.addstr(
                        whale_row + 2,
                        2,
                        (
                            f"Levels Cleared : {whale_levels}"
                        )[:max(1, width - 4)],
                    )

                if whale_row + 3 < height:
                    side_name = (
                        "BUY"
                        if whale_side == OrderSide.BUY
                        else "SELL"
                    )

                    stdscr.addstr(
                        whale_row + 3,
                        2,
                        (
                            f"Whale Side     : {side_name}"
                        )[:max(1, width - 4)],
                    )

                if whale_row + 4 < height:
                    stdscr.addstr(
                        whale_row + 4,
                        2,
                        (
                            f"Quantity       : {whale_quantity}"
                        )[:max(1, width - 4)],
                    )

            # -------------------------------------------------
            # Statistics
            # -------------------------------------------------

            stats_row = 26

            if stats_row < height:
                stdscr.addstr(
                    stats_row,
                    2,
                    f"Best Bid        : {best_bid}",
                )

            if stats_row + 1 < height:
                stdscr.addstr(
                    stats_row + 1,
                    2,
                    f"Best Ask        : {best_ask}",
                )

            if stats_row + 2 < height:
                stdscr.addstr(
                    stats_row + 2,
                    2,
                    f"Spread          : {spread}",
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
                    f"Frame Latency   : {frame_latency_us:.3f} us",
                )

            # -------------------------------------------------
            # Footer
            # -------------------------------------------------

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
    