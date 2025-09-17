from abc import ABC, abstractmethod
from enum import Enum

from coincurve import PrivateKey

from zex.sdk.data_types import CancelOrderRequest, PlaceOrderRequest, WithdrawRequest


class SignatureType(Enum):
    SECP256K1 = 1
    ED25519 = 2


class SigningVisitor(ABC):
    def __init__(
        self,
        api_key: str | None = None,
    ) -> None:
        private_key_bytes = bytes.fromhex(api_key) if api_key is not None else None
        self._private_key = PrivateKey(secret=private_key_bytes)
        self.public_key = self._private_key.public_key.format(compressed=True)

        self._version = 1
        self._signature_type = SignatureType.SECP256K1

        self._register_command = ord("r")
        self._buy_command = ord("b")
        self._sell_command = ord("s")
        self._cancel_command = ord("c")
        self._withdraw_command = ord("w")
        self._deposit_command = ord("d")
        self._btc_deposit_command = ord("x")

        self._price_digits = 2
        self._volume_digits = 5

    @abstractmethod
    def create_register_transaction(self) -> bytes:
        pass

    @abstractmethod
    def create_place_order_transaction(
        self, request: PlaceOrderRequest, nonce: int, user_id: int
    ) -> bytes:
        pass

    @abstractmethod
    def create_cancel_order_transaction(
        self, request: CancelOrderRequest, user_id: int
    ) -> bytes:
        pass

    @abstractmethod
    def create_withdraw_transaction(
        self, request: WithdrawRequest, nonce: int, user_id: int
    ) -> bytes:
        pass

    def _create_register_message(self) -> bytes:
        message = "Welcome to ZEX."
        message = "".join(
            ("\x19Ethereum Signed Message:\n", str(len(message)), message)
        )
        return message.encode("ascii")
