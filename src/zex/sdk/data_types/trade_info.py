from pydantic import BaseModel, Field


class TradeInfo(BaseModel):
    name: str = Field(..., description="Identifier or label for the trade.")
    t: float = Field(..., description="Timestamp of the trade.")  # noqa: VNE001
    base_token: str = Field(..., description="Symbol of the base token.")
    quote_token: str = Field(..., description="Symbol of the quote token.")
    amount: float = Field(..., description="Amount of the base token traded.")
    price: float = Field(..., description="Trade execution price per unit.")
    nonce: int = Field(..., description="Unique nonce value to track the trade.")
