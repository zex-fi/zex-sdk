from pydantic import BaseModel, Field


class Order(BaseModel):
    name: str = Field(..., description="Unique identifier for the order.")
    base_token: str = Field(..., description="Symbol of the base token (e.g., 'ETH').")
    quote_token: str = Field(
        ..., description="Symbol of the quote token (e.g., 'USDT')."
    )
    ammount: float = Field(..., description="Amount of base token to be traded.")
    price: float = Field(..., description="Price per unit of the base token.")
    t: float = Field(..., description="Timestamp of the order.")  # noqa: VNE001
    nonce: int = Field(
        ..., description="Unique number to ensure order uniqueness and prevent replay."
    )
    slice: str = Field(..., description="Order slicing information, if applicable.")
