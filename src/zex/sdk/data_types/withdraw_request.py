from pydantic import BaseModel


class WithdrawRequest(BaseModel):
    token_chain: str
    token_name: str
    amount: str
    destination: str
