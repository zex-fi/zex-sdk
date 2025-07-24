from pydantic import BaseModel, Field


class Withdraw(BaseModel):
    chain: str = Field(..., description="Blockchain network used for withdrawal.")
    tokenContract: str = Field(  # noqa: N815
        ..., description="Address of the token's smart contract."
    )
    amount: str = Field(
        ..., description="Amount of token withdrawn (as string to preserve precision)."
    )
    destination: str = Field(..., description="Destination wallet address.")
    user_id: int = Field(
        ..., description="ID of the user who requested the withdrawal."
    )
    t: float = Field(  # noqa: VNE001
        ..., description="Timestamp of the withdrawal event."
    )
    id: int = Field(..., description="Unique identifier of the withdrawal transaction.")
