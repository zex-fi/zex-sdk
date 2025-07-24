from pydantic import BaseModel, Field


class Transfer(BaseModel):
    chain: str = Field(
        ..., description="Name of the blockchain where the transfer occurred."
    )
    token: str = Field(
        ..., description="Symbol or identifier of the transferred token."
    )
    txHash: str = Field(  # noqa: N815
        ..., description="Transaction hash on the blockchain."
    )
    amount: float = Field(..., description="Amount of token transferred.")
    time: float = Field(..., description="Timestamp of the transfer.")
