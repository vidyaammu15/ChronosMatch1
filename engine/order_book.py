from collections import defaultdict, deque

from core.types import Order, OrderSide


class LimitOrderBook:
    def __init__(self):
        # Price → queue of orders
        self.bids = defaultdict(deque)
        self.asks = defaultdict(deque)

    def add_order(self, order: Order):
        """Add an order to the appropriate side of the book."""

        if order.side == OrderSide.BUY:
            self.bids[order.price].append(order)

        elif order.side == OrderSide.SELL:
            self.asks[order.price].append(order)

        else:
            raise ValueError(f"Unsupported order side: {order.side}")

    def best_bid(self):
        """Return the highest BUY price, or None if empty."""

        if not self.bids:
            return None

        return max(self.bids.keys())

    def best_ask(self):
        """Return the lowest SELL price, or None if empty."""

        if not self.asks:
            return None

        return min(self.asks.keys())

    def bid_quantity(self, price):
        """Return total quantity available at a BUY price."""

        return sum(
            order.quantity
            for order in self.bids.get(price, [])
        )

    def ask_quantity(self, price):
        """Return total quantity available at a SELL price."""

        return sum(
            order.quantity
            for order in self.asks.get(price, [])
        )

    def remove_order(self, order: Order):
        """Remove an order from the book."""

        book = (
            self.bids
            if order.side == OrderSide.BUY
            else self.asks
        )

        queue = book.get(order.price)

        if queue is None:
            return False

        try:
            queue.remove(order)
        except ValueError:
            return False

        if not queue:
            del book[order.price]

        return True

    def cancel_order(self, order: Order):
        """Cancel an existing order."""

        return self.remove_order(order)