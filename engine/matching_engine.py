from dataclasses import dataclass

from core.types import Order, OrderSide
from engine.order_book import LimitOrderBook


@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: int
    quantity: int


class MatchingEngine:
    def __init__(self):
        self.book = LimitOrderBook()

    def process_order(self, order: Order):
        """Process an incoming order and return generated trades."""

        trades = []

        if order.side == OrderSide.BUY:
            trades = self._match_buy(order)
        elif order.side == OrderSide.SELL:
            trades = self._match_sell(order)
        else:
            raise ValueError(f"Unsupported order side: {order.side}")

        return trades

    def _match_buy(self, incoming: Order):
        trades = []

        while incoming.quantity > 0:
            best_ask = self.book.best_ask()

            if best_ask is None:
                break

            # No match if BUY price is below SELL price.
            if incoming.price < best_ask:
                break

            queue = self.book.asks[best_ask]

            resting = queue[0]

            trade_quantity = min(
                incoming.quantity,
                resting.quantity,
            )

            trades.append(
                Trade(
                    buy_order_id=incoming.order_id,
                    sell_order_id=resting.order_id,
                    price=resting.price,
                    quantity=trade_quantity,
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

    def _match_sell(self, incoming: Order):
        trades = []

        while incoming.quantity > 0:
            best_bid = self.book.best_bid()

            if best_bid is None:
                break

            # No match if SELL price is above BUY price.
            if incoming.price > best_bid:
                break

            queue = self.book.bids[best_bid]

            resting = queue[0]

            trade_quantity = min(
                incoming.quantity,
                resting.quantity,
            )

            trades.append(
                Trade(
                    buy_order_id=resting.order_id,
                    sell_order_id=incoming.order_id,
                    price=resting.price,
                    quantity=trade_quantity,
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