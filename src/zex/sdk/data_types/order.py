from typing import Literal

from pydantic import BaseModel, Field


class Order(BaseModel):
    amount: float = Field(..., description="Amount of base token to be traded.")
    base_token: str = Field(..., description="Symbol of the base token (e.g., 'ETH').")
    id: int = Field(..., description="Unique identifier for the order.")
    name: Literal["buy", "sell"] = Field(
        ..., description="The name or side of the order."
    )
    nonce: int = Field(
        ..., description="Unique number to ensure order uniqueness and prevent replay."
    )
    price: float = Field(..., description="Price per unit of the base token.")
    quote_token: str = Field(
        ..., description="Symbol of the quote token (e.g., 'USDT')."
    )
    t: float = Field(..., description="Timestamp of the order.")  # noqa: VNE001
