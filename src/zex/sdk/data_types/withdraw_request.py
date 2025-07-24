from pydantic import BaseModel, Field


class WithdrawRequest(BaseModel):
    token_chain: str = Field(
        ..., description="Blockchain network where the token resides."
    )
    token_name: str = Field(..., description="Symbol or name of the token to withdraw.")
    amount: str = Field(
        ...,
        description="Amount of token to withdraw (as string to preserve precision).",
    )
    destination: str = Field(..., description="Destination address for the withdrawal.")
