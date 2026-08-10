from dataclasses import dataclass
from enum import IntEnum


class OrderSide(IntEnum):
    BUY = 1
    SELL = 2


@dataclass
class Order:
    order_id: int
    side: OrderSide
    price: int
    quantity: int
    timestamp: int