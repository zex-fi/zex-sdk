from typing import Literal

from pydantic import BaseModel, Field


class TradeInfo(BaseModel):
    amount: float = Field(..., description="Amount of the base token traded.")
    base_token: str = Field(..., description="Symbol of the base token.")
    id: int = Field(..., description="The ID of the trade.")
    maker_order_id: int = Field(..., description="The ID of the corresponding order.")
    name: Literal["buy", "sell"] = Field(
        ..., description="Whether it was a buy or sell trade."
    )
    price: float = Field(..., description="Trade execution price per unit.")
    quote_token: str = Field(..., description="Symbol of the quote token.")
    t: float = Field(..., description="Timestamp of the trade.")  # noqa: VNE001
    taker_order_id: int = Field(
        ..., description="The ID of the taker order of this trade."
    )
