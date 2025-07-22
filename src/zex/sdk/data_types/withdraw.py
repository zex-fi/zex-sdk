from pydantic import BaseModel


class Withdraw(BaseModel):
    chain: str
    tokenContract: str
    amount: str
    destination: str
    user_id: int
    t: float
    id: int
