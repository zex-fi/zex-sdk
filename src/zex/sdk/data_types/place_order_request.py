from enum import Enum

from pydantic import BaseModel


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PlaceOrderRequest(BaseModel):
    base_token: str
    quote_token: str
    side: OrderSide
    volume: float
    price: float
