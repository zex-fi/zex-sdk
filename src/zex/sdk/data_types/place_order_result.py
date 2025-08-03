from pydantic import BaseModel, Field

from zex.sdk.data_types.place_order_request import PlaceOrderRequest


class PlaceOrderResult(BaseModel):
    place_order_request: PlaceOrderRequest = Field(
        ..., description="The place order request data class."
    )
    nonce: int = Field(..., description="The nonce of the placed order.")
    signed_order_transaction: bytes = Field(
        ..., description="The signed transaction sent to the exchange server."
    )
