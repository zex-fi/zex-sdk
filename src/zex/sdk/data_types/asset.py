from pydantic import BaseModel


class Asset(BaseModel):
    asset: str
    free: str
    locked: str
    freeze: str
    withdrawing: str
