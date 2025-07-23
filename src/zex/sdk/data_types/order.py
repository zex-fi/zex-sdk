from pydantic import BaseModel


class Order(BaseModel):
    name: str
    base_token: str
    quote_token: str
    ammount: float
    price: float
    t: float  # noqa: VNE001
    nonce: int
    slice: str
