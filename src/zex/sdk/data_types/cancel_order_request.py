from pydantic import BaseModel, Field


class CancelOrderRequest(BaseModel):
    signed_order: bytes = Field(
        ..., description="The signature of the placed order to be cancelled."
    )
    order_nonce: int = Field(..., description="The nonce of the order to be cancelled.")
