from pydantic import BaseModel


class Transfer(BaseModel):
    chain: str
    token: str
    txHash: str  # noqa: N815
    amount: float
    time: float
