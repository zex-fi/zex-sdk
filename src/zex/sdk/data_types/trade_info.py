from pydantic import BaseModel


class TradeInfo(BaseModel):
    name: str
    t: float  # noqa: VNE001
    base_token: str
    quote_token: str
    amount: float
    price: float
    nonce: int
