from pydantic import BaseModel


class Transfer(BaseModel):
    chain: str
    token: str
    txHash: str
    amount: float
    time: float
