from dataclasses import dataclass
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class PlaceOrderRequest:
    base_token: str
    quote_token: str
    side: OrderSide
    volume: float
    price: float
