from abc import ABC, abstractmethod
from coincurve import PrivateKey
from enum import Enum

from zex.sdk.data_types import CancelOrderRequest, PlaceOrderRequest, WithdrawRequest


class SignatureType(Enum):
    SECP256K1 = 1
    ED25519 = 2


class SigningVisitor(ABC):
    def __init__(self, api_key: str | None = None,) -> None:
        private_key_bytes = bytes.fromhex(api_key) if api_key is not None else None
        self._private_key = PrivateKey(secret=private_key_bytes)
        self.public_key = self._private_key.public_key.format(compressed=True)

        self._version = 1
        self._signature_type = SignatureType

        self._register_command = ord("r")
        self._buy_command = ord("b")
        self._sell_command = ord("s")
        self._cancel_command = ord("c")
        self._withdraw_command = ord("w")
        self._deposit_command = ord("d")
        self._btc_deposit_command = ord("x")

    @abstractmethod
    def create_register_signature(self) -> None:
        pass

    @abstractmethod
    def create_signed_order_transaction(self, request: PlaceOrderRequest) -> bytes:
        pass

    @abstractmethod
    def create_sigend_cancel_order_transaction(
        self, request: CancelOrderRequest
    ) -> bytes:
        pass

    @abstractmethod
    def create_signed_withdraw_transaction(
        self, request: WithdrawRequest
    ) -> bytes:
        pass
