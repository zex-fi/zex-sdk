from pydantic import BaseModel


class Withdraw(BaseModel):
    chain: str
    tokenContract: str  # noqa: N815
    amount: str
    destination: str
    user_id: int
    t: float  # noqa: VNE001
    id: int
