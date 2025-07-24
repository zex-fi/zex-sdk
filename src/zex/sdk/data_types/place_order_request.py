from enum import Enum

from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PlaceOrderRequest(BaseModel):
    base_token: str = Field(..., description="Symbol of the base token for the order.")
    quote_token: str = Field(
        ..., description="Symbol of the quote token for the order."
    )
    side: OrderSide = Field(..., description="Side of the order: 'buy' or 'sell'.")
    volume: float = Field(..., description="Amount of base token to be bought or sold.")
    price: float = Field(..., description="Limit price per unit of the base token.")
