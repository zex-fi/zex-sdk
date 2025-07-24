from pydantic import BaseModel, Field


class Asset(BaseModel):
    asset: str = Field(..., description="The symbol of the asset (e.g., 'BTC', 'ETH').")
    free: str = Field(
        ..., description="Amount of the asset that is available for trading."
    )
    locked: str = Field(
        ..., description="Amount of the asset that is locked in orders."
    )
    freeze: str = Field(
        ...,
        description=(
            "Amount of the asset that is frozen due to other reasons (e.g., compliance"
            " holds)."
        ),
    )
    withdrawing: str = Field(
        ..., description="Amount of the asset currently being withdrawn."
    )
