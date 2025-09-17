import time
from struct import pack

import numpy as np
from eth_hash.auto import keccak

from zex.sdk.client.signing_visitor import SigningVisitor
from zex.sdk.data_types import (
    CancelOrderRequest,
    OrderSide,
    PlaceOrderRequest,
    WithdrawRequest,
)


class SigningVisitorMain(SigningVisitor):
    def create_register_transaction(self) -> bytes:
        transaction_data = (
            pack(">B", self._version)
            + pack(">B", self._register_command)
            + self.public_key
        )
        signature = self._private_key.sign_recoverable(
            keccak(self._create_register_message()), hasher=None
        )
        signature = signature[:64]  # Compact format.
        transaction_data += signature
        return transaction_data

    def create_place_order_transaction(
        self, request: PlaceOrderRequest, nonce: int, user_id: int
    ) -> bytes:
        pair = request.base_token + request.quote_token
        transaction_data = (
            pack(">B", self._version)
            + pack(
                ">B",
                (
                    self._buy_command
                    if request.side == OrderSide.BUY
                    else self._sell_command
                ),
            )
            + pack(">B", len(request.base_token))
            + pack(">B", len(request.quote_token))
            + pair.encode()
            + pack(">d", request.volume)
            + pack(">d", request.price)
        )
        epoch = int(time.time())

        transaction_data += pack(">II", epoch, nonce) + pack(">Q", user_id)

        message = (
            "v: 1\n"
            f"name: {request.side.lower()}\n"
            f"base token: {request.base_token}\n"
            f"quote token: {request.quote_token}\n"
            f"amount: {np.format_float_positional(request.volume, trim='0')}\n"
            f"price: {np.format_float_positional(request.price, trim='0')}\n"
            f"t: {epoch}\n"
            f"nonce: {nonce}\n"
            f"user_id: {user_id}\n"
        )
        message = "\x19Ethereum Signed Message:\n" + str(len(message)) + message

        signature = self._private_key.sign_recoverable(
            keccak(message.encode("ascii")), hasher=None
        )
        signature = signature[:64]  # Compact format

        transaction_data += signature
        return transaction_data

    def create_cancel_order_transaction(
        self, request: CancelOrderRequest, user_id: int
    ) -> bytes:
        transaction_data = (
            pack(">B", self._version)
            + pack(">B", self._cancel_command)
            + request.signed_order[1:-72]
            + pack(">Q", user_id)
        )

        message = (
            f"v: {transaction_data[0]}\n"
            "name: cancel\n"
            f"slice: {request.signed_order[1:-72].hex()}\n"
            f"user_id: {user_id}\n"
        )
        message = "".join(
            ("\x19Ethereum Signed Message:\n", str(len(message)), message)
        )

        signature = self._private_key.sign_recoverable(
            keccak(message.encode("ascii")), hasher=None
        )
        signature = signature[:64]  # Compact format

        transaction_data += signature
        return transaction_data

    def create_withdraw_transaction(
        self, request: WithdrawRequest, nonce: int, user_id: int
    ) -> bytes:
        transaction_data = (
            pack(">B", self._version)
            + pack(">B", self._withdraw_command)
            + pack(">B", len(request.token_name))
            + request.token_chain.encode()
            + request.token_name.encode()
            + pack(">d", request.amount)
            + bytes.fromhex(request.destination[2:])
        )
        epoch = int(time.time())
        transaction_data += (
            pack(">II", epoch, nonce) + pack(">Q", user_id) + self.public_key
        )

        message = (
            "v: 1\n"
            "name: withdraw\n"
            f"token chain: {request.token_chain}\n"
            f"token name: {request.token_name}\n"
            f"amount: {request.amount}\n"
            f"to: {request.destination}\n"
            f"t: {epoch}\n"
            f"nonce: {nonce}\n"
            f"user_id: {user_id}\n"
            f"public: {self.public_key.hex()}\n"
        )
        message = "\x19Ethereum Signed Message:\n" + str(len(message)) + message

        signature = self._private_key.sign_recoverable(
            keccak(message.encode("ascii")), hasher=None
        )
        signature = signature[:64]  # Compact format

        transaction_data += signature
        return transaction_data
