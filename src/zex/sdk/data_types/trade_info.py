from pydantic import BaseModel


class TradeInfo(BaseModel):
    name: str
    t: float
    base_token: str
    quote_token: str
    amount: float
    price: float
    nonce: int
