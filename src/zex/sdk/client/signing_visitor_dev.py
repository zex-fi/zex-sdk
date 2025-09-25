import time
from decimal import Decimal
from struct import pack

from eth_hash.auto import keccak

from zex.sdk.client.signing_visitor import SigningVisitor
from zex.sdk.data_types import (
    CancelOrderRequest,
    OrderSide,
    PlaceOrderRequest,
    WithdrawRequest,
)


class SigningVisitorDev(SigningVisitor):
    def create_register_transaction(self) -> bytes:
        transaction_data = (
            pack(">B", self._version)
            + pack(">B", self._register_command)
            + pack(">B", self._signature_type.value)
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

        price = round(Decimal(request.price), self._price_digits)
        volume = round(Decimal(request.volume), self._volume_digits)
        volume_mantissa, volume_exponent = self._to_scientific(volume)
        price_mantissa, price_exponent = self._to_scientific(price)

        volume = volume_mantissa * 10 ** Decimal(volume_exponent)
        price = price_mantissa * 10 ** Decimal(price_exponent)
        epoch = int(time.time())

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
            + pack(">B", self._signature_type.value)
            + pack(">B", len(request.base_token))
            + pack(">B", len(request.quote_token))
            + pair.encode()
            + pack(">Q b", volume_mantissa, volume_exponent)
            + pack(">Q b", price_mantissa, price_exponent)
            + pack(">IQ", epoch, nonce)
            + pack(">Q", user_id)
        )

        message = (
            "v: 1\n"
            f"name: {request.side.lower()}\n"
            f"base token: {request.base_token}\n"
            f"quote token: {request.quote_token}\n"
            f"amount: {self._format_decimal(volume)}\n"
            f"price: {self._format_decimal(price)}\n"
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
            + pack(">B", self._signature_type.value)
            + pack(">Q", user_id)
            + pack(">Q", request.order_nonce)
        )

        message = (
            f"v: {transaction_data[0]}\n"
            "name: cancel\n"
            f"user_id: {user_id}\n"
            f"order_nonce: {request.order_nonce}\n"
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
            + pack(">B", self._signature_type.value)
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
        )
        message = "\x19Ethereum Signed Message:\n" + str(len(message)) + message

        signature = self._private_key.sign_recoverable(
            keccak(message.encode("ascii")), hasher=None
        )
        signature = signature[:64]  # Compact format

        transaction_data += signature
        return transaction_data

    @staticmethod
    def _to_scientific(number: Decimal) -> tuple[int, int]:
        """Convert a Decimal value to a mantissa and an exponent (base 10)."""

        sign, digits, exponent = number.normalize().as_tuple()
        if not isinstance(exponent, int):
            raise TypeError(f"Cannot convert value to scientific form: {number}")

        mantissa = 0
        for index, digit in enumerate(reversed(digits)):
            mantissa += digit * 10**index
        mantissa *= -1 if sign != 0 else 1

        if exponent < -128 or exponent > 127:
            raise RuntimeError(f"Cannot convert value to scientific form: {number}")

        return mantissa, exponent

    @staticmethod
    def _format_decimal(decimal_number: Decimal) -> str:
        """
        Format the given decimal number, making sure scientific notation \
        is *not* used and that there's always a traling .0 if there's no \
        fractional part.
        """
        result = format(decimal_number, "f")
        if "." not in result:
            result += ".0"
        return result
