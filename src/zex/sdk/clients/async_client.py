import time
from collections.abc import Iterable
from struct import pack

import httpx
from coincurve import PrivateKey
from eth_hash.auto import keccak

from zex.sdk.clients.order import Order, OrderSide


class AsyncClient:
    def __init__(
        self,
        api_key: str | None = None,
        testnet: bool = True,
    ) -> None:
        self._api_endpoint = "https://api.zex.finance"
        self._version = 1
        self._testnet = testnet

        private_key_bytes = bytes.fromhex(api_key) if api_key is not None else None
        self._private_key = PrivateKey(secret=private_key_bytes)
        self._public_key = self._private_key.public_key.format(compressed=True)
        self._register_timeout = 20.0
        self._nonce: int | None = None
        self.user_id: int | None = None

        self._register_command = ord("r")
        self._buy_command = ord("b")
        self._sell_command = ord("s")
        self._cancel_command = ord("c")

    async def place_batch_order(self, orders: Iterable[Order]) -> None:
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")

        orders = list(orders)

        if len(orders) == 0:
            return

        async with httpx.AsyncClient() as client:
            nonce_response = await client.get(
                f"{self._api_endpoint}/v1/user/nonce?id={self.user_id}"
            )
            self._nonce = nonce_response.json()["nonce"]
            assert self._nonce is not None, "For typing."

        payload = []
        for order in orders:
            signed_order = self._create_signed_order(order)
            self._nonce += 1
            payload.append(signed_order.decode("latin-1"))

        if not payload:
            return

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/order",
                json=payload,
            )

    async def cancel_batch_order(self, signed_orders: Iterable[bytes]) -> None:
        payload = []
        for signed_order in signed_orders:
            payload.append(self._create_sigend_cancel_order(signed_order))
        if not payload:
            return
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/order",
                json=payload,
            )

    def _create_signed_order(self, order: Order) -> bytes:
        assert self._nonce is not None

        pair = order.base_token + order.quote_token
        transaction_data = (
            pack(">B", self._version)
            + pack(
                ">B",
                (
                    self._buy_command
                    if order.side == OrderSide.BUY
                    else self._sell_command
                ),
            )
            + pack(">B", len(order.base_token))
            + pack(">B", len(order.quote_token))
            + pair.encode()
            + pack(">d", order.volume)
            + pack(">d", order.price)
        )
        epoch = int(time.time())

        transaction_data += pack(">II", epoch, self._nonce) + self._public_key

        message = (
            "v: 1\n"
            f"name: {order.side.lower()}\n"
            f"base token: {order.base_token}\n"
            f"quote token: {order.quote_token}\n"
            f"amount: {order.volume:g}\n"
            f"price: {order.price}\n"
            f"t: {epoch}\n"
            f"nonce: {self._nonce}\n"
            f"public: {self._public_key.hex()}\n"
        )
        message = "\x19Ethereum Signed Message:\n" + str(len(message)) + message

        signature = self._private_key.sign_recoverable(
            keccak(message.encode("ascii")), hasher=None
        )
        signature = signature[:64]  # Compact format

        transaction_data += signature
        return transaction_data

    def _create_sigend_cancel_order(self, signed_order: bytes) -> bytes:
        transaction_data = (
            pack(">B", self._version)
            + pack(">B", self._cancel_command)
            + signed_order[1:-97]
            + self._public_key
        )

        message = (
            f"v: {transaction_data[0]}\n"
            "name: cancel\n"
            f"slice: {signed_order[1:-97].hex()}\n"
            f"public: {signed_order[-97:-64].hex()}\n"
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
