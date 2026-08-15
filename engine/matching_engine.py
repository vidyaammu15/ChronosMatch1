from dataclasses import dataclass
import time

from core.ctypes_types import COrder, c_to_order
from core.types import Order, OrderSide
from engine.order_book import LimitOrderBook


@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: int
    quantity: int
    engine_enter_ns: int = 0
    engine_exit_ns: int = 0
    latency_ns: int = 0


class MatchingEngine:
    def __init__(self):
        self.book = LimitOrderBook()

    def process_order(self, order: Order):
        """Process a normal Python Order with nanosecond timing."""

        engine_enter_ns = time.perf_counter_ns()

        if order.side == OrderSide.BUY:
            return self._match_buy(
                order,
                engine_enter_ns,
            )

        if order.side == OrderSide.SELL:
            return self._match_sell(
                order,
                engine_enter_ns,
            )

        raise ValueError(
            f"Unsupported order side: {order.side}"
        )

    def process_c_order(self, c_order: COrder):
        """
        Process a C-compatible order.

        The C-compatible structure is converted at the
        matching-engine boundary so the existing order-book
        implementation remains compatible.
        """
        if not isinstance(c_order, COrder):
            raise TypeError(
                "process_c_order expects a COrder"
            )

        order = c_to_order(c_order)

        return self.process_order(order)

    def cancel_order(self, order: Order):
        """Cancel a resting order."""
        return self.book.cancel_order(order)

    def _match_buy(
        self,
        incoming: Order,
        engine_enter_ns: int,
    ):
        trades = []

        while incoming.quantity > 0:
            best_ask = self.book.best_ask()

            if best_ask is None:
                break

            if incoming.price < best_ask:
                break

            queue = self.book.asks[best_ask]
            resting = queue[0]

            trade_quantity = min(
                incoming.quantity,
                resting.quantity,
            )

            engine_exit_ns = time.perf_counter_ns()

            trades.append(
                Trade(
                    buy_order_id=incoming.order_id,
                    sell_order_id=resting.order_id,
                    price=resting.price,
                    quantity=trade_quantity,
                    engine_enter_ns=engine_enter_ns,
                    engine_exit_ns=engine_exit_ns,
                    latency_ns=(
                        engine_exit_ns - engine_enter_ns
                    ),
                )
            )

            incoming.quantity -= trade_quantity
            resting.quantity -= trade_quantity

            if resting.quantity == 0:
                queue.popleft()

                if not queue:
                    del self.book.asks[best_ask]

        if incoming.quantity > 0:
            self.book.add_order(incoming)

        return trades

    def _match_sell(
        self,
        incoming: Order,
        engine_enter_ns: int,
    ):
        trades = []

        while incoming.quantity > 0:
            best_bid = self.book.best_bid()

            if best_bid is None:
                break

            if incoming.price > best_bid:
                break

            queue = self.book.bids[best_bid]
            resting = queue[0]

            trade_quantity = min(
                incoming.quantity,
                resting.quantity,
            )

            engine_exit_ns = time.perf_counter_ns()

            trades.append(
                Trade(
                    buy_order_id=resting.order_id,
                    sell_order_id=incoming.order_id,
                    price=resting.price,
                    quantity=trade_quantity,
                    engine_enter_ns=engine_enter_ns,
                    engine_exit_ns=engine_exit_ns,
                    latency_ns=(
                        engine_exit_ns - engine_enter_ns
                    ),
                )
            )

            incoming.quantity -= trade_quantity
            resting.quantity -= trade_quantity

            if resting.quantity == 0:
                queue.popleft()

                if not queue:
                    del self.book.bids[best_bid]

        if incoming.quantity > 0:
            self.book.add_order(incoming)

        return trades
