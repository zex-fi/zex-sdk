from __future__ import annotations

import asyncio
import time
from collections.abc import Iterable
from struct import pack
from typing import Any, TypeVar

import httpx
from coincurve import PrivateKey
from eth_hash.auto import keccak
from pydantic import TypeAdapter

from zex.sdk.data_types import (
    Asset,
    Order,
    OrderSide,
    PlaceOrderRequest,
    PlaceOrderResult,
    TradeInfo,
    Transfer,
    Withdraw,
    WithdrawRequest,
)

ServerResponseType = TypeVar("ServerResponseType")


class AsyncClient:
    """
    The asynchronous client of Zex exchange supporting the main functionalities \
    of the exchange API.
    """

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
        self.public_key = self._private_key.public_key.format(compressed=True)
        self._register_timeout = 20.0
        self.nonce: int | None = None
        self.user_id: int | None = None

        self._register_command = ord("r")
        self._buy_command = ord("b")
        self._sell_command = ord("s")
        self._cancel_command = ord("c")
        self._withdraw_command = ord("w")
        self._deposit_command = ord("d")
        self._btc_deposit_command = ord("x")

    @classmethod
    async def create(
        cls, api_key: str | None = None, testnet: bool = True
    ) -> AsyncClient:
        """
        Create a registered instance of asynchronous Zex client to use functionalities \
        provided by the Zex exchange.

        .. warning::
            The user of this class should only use this method to instantiate. The
            `__init__` method of this class is for internal use only.

        :param api_key: The API key used to register with Zex exchange servers and sign \
        the transactions.
        :param testnet: Whether or not to submit transactions into Zex testnet.
        """
        client = cls(api_key, testnet)
        await client.register_user_id()
        return client

    async def register_user_id(self) -> None:
        """
        Register the user ID with Zex exchange. Some methods the client to be registered \
        to be able to take effect in Zex server.

        .. note:
            The :py:meth:`~AsyncClient.create` method automatically calls this method and registers
            the client.
        """
        if self.user_id is not None:
            return

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

        user_id = None
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/register",
                json=[transaction_data.decode("latin-1")],
                timeout=self._register_timeout,
            )
            try:
                user_id = await asyncio.wait_for(
                    self._fetch_user_id_from_server(client),
                    timeout=self._register_timeout,
                )
            except asyncio.TimeoutError as exc:
                raise RuntimeError("Registering user ID timed out.") from exc
        self.user_id = user_id

    async def place_batch_order(
        self, orders: Iterable[PlaceOrderRequest]
    ) -> Iterable[PlaceOrderResult]:
        """
        Place a batch of orders in Zex exchange.

        .. note:
            The client should be registered before calling this method.

        :param orders: The batch of orders to be placed in the exchange.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")

        orders = list(orders)

        if len(orders) == 0:
            return []

        async with httpx.AsyncClient() as client:
            nonce_response = await client.get(
                f"{self._api_endpoint}/v1/user/nonce?id={self.user_id}"
            )
            self.nonce = nonce_response.json()["nonce"]
            assert self.nonce is not None, "For typing."

        payload = []
        place_order_results = []
        for order in orders:
            signed_order = self._create_signed_order_transaction(order)
            place_order_results.append(
                PlaceOrderResult(
                    place_order_request=order,
                    nonce=self.nonce,
                    signed_order_transaction=signed_order,
                )
            )
            self.nonce += 1
            payload.append(signed_order.decode("latin-1"))

        if not payload:
            return []

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/order",
                json=payload,
            )

        return place_order_results

    async def cancel_batch_order(self, signed_placed_orders: Iterable[bytes]) -> None:
        """
        Cancel a batch of orders in Zex exchange.

        .. note:
            The client should be registered before calling this method.

        :param signed_orders: The batch signed order transactions that were placed in \
            the exchange to be canceled.
        """
        payload = []
        for signed_placed_order in signed_placed_orders:
            signed_order = self._create_sigend_cancel_order_transaction(
                signed_placed_order
            )
            payload.append(signed_order.decode("latin-1"))
        if not payload:
            return
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/order",
                json=payload,
            )

    async def withdraw(self, withdraw_request: WithdrawRequest) -> None:
        """
        Withdraw from Zex exchange.

        .. note:
            The client should be registered before calling this method.

        :param withdraw_request: The withdraw request containing the required fields.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")

        async with httpx.AsyncClient() as client:
            nonce_response = await client.get(
                f"{self._api_endpoint}/v1/user/nonce?id={self.user_id}"
            )
            self.nonce = nonce_response.json()["nonce"]
            assert self.nonce is not None, "For typing."

        signed_withdraw_transaction = self._create_signed_withdraw_transaction(
            withdraw_request
        )
        payload = [signed_withdraw_transaction.decode("latin-1")]
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/withdraw",
                json=payload,
            )

    async def deposit(self, transaction: bytes) -> None:
        """
        Deposit in Zex exchange.

        .. note:
            The client should be registered before calling this method.

        :param transaction: The signed transaction for depositing in Zex exchange.
        """
        payload = [transaction.decode("latin-1")]
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/deposit",
                json=payload,
            )

    async def get_server_time(self) -> int:
        """Get the server time."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_endpoint}/v1/time",
            )
        response_data: dict[str, int] = response.json()
        time = response_data.get("serverTime")
        if time is None:
            raise RuntimeError("The server did not return a proper response.")
        return time

    async def ping(self) -> bool:
        """Whether the server responds to a ping request."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_endpoint}/v1/ping",
            )
        if response.status_code == 200:
            return True
        return False

    async def get_price(self, symbol: str) -> float:
        """
        Get the price of a market.

        :param symbol: The symbol of the market whose price to query.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_endpoint}/v1/ticker/price",
                params={"symbol": symbol},
            )
        response_data = response.json()
        if response.status_code == 422:
            detail = response_data.get("detail") or []
            raise RuntimeError(f"Fetching price from the server failed: {detail}")
        price: float | None = response_data.get("price")
        if price is None:
            raise RuntimeError(
                "Could not retrieve the price of symbol from the server."
            )
        return price

    async def get_ticker(self, symbol: str) -> dict[str, Any]:
        """
        Get the ticker of a certain market.

        :param symbol: The symbol of the market to get the ticker of.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_endpoint}/v1/ticker",
                params={"symbol": symbol},
            )
        response_data: dict[str, Any] = response.json()
        if response.status_code == 422:
            detail = response_data.get("detail") or []
            raise RuntimeError(f"Fetching ticker from the server failed: {detail}")
        return response_data

    async def get_depth(self, symbol: str, limit: int) -> dict[str, Any]:
        """
        Get the market depth.

        :param symbol: The symbol of the market to get the depth of.
        :param limit: The limit of the queried depth.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_endpoint}/v1/depth",
                params={"symbol": symbol, "limit": limit},
            )
        response_data: dict[str, Any] = response.json()
        if response.status_code == 422:
            detail = response_data.get("detail") or []
            raise RuntimeError(
                f"Fetching market depth from the server failed: {detail}"
            )
        return response_data

    async def get_exchange_info(self, symbol: str) -> dict[str, Any]:
        """
        Get the exchange info for a specified market.

        :parma symbol: The symbol of the market to get the exchange info of.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_endpoint}/v1/exchangeInfo",
                params={"symbol": symbol},
            )
        response_data: dict[str, Any] = response.json()
        if response.status_code == 422:
            detail = response_data.get("detail") or []
            raise RuntimeError(
                f"Fetching exchange info from the server failed: {detail}"
            )
        return response_data

    async def get_user_trades(self) -> list[TradeInfo]:
        """
        Get the list of all trades of the user.

        .. note:
            The client should be registered before calling this method.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")
        return await self._get_and_parse_response_from_server(
            type_adapter=TypeAdapter(list[TradeInfo]),
            api_path="/v1/user/trades",
            params={"id": self.user_id},
        )

    async def get_user_assets(self) -> list[Asset]:
        """
        Get the list of all assets of the user.

        .. note:
            The client should be registered before calling this method.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")
        return await self._get_and_parse_response_from_server(
            type_adapter=TypeAdapter(list[Asset]),
            api_path="/v1/asset/getUserAsset",
            params={"id": self.user_id},
        )

    async def get_user_orders(self) -> list[Order]:
        """
        Get the list of all the placed orders of the user.

        .. note:
            The client should be registered before calling this method.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")
        return await self._get_and_parse_response_from_server(
            type_adapter=TypeAdapter(list[Order]),
            api_path="/v1/user/orders",
            params={"id": self.user_id},
        )

    async def get_user_transfers(self) -> list[Transfer]:
        """
        Get the list of all transfers of the user.

        .. note:
            The client should be registered before calling this method.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")
        return await self._get_and_parse_response_from_server(
            type_adapter=TypeAdapter(list[Transfer]),
            api_path="/v1/user/transfers",
            params={"id": self.user_id},
        )

    async def get_user_withdraws(self, chain: str) -> list[Withdraw]:
        """
        Get the list of all withdraws of the user.

        .. note:
            The client should be registered before calling this method.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")
        return await self._get_and_parse_response_from_server(
            type_adapter=TypeAdapter(list[Withdraw]),
            api_path="/v1/user/withdraws",
            params={"id": self.user_id, "chain": chain},
        )

    def _create_register_message(self) -> bytes:
        message = "Welcome to ZEX."
        message = "".join(
            ("\x19Ethereum Signed Message:\n", str(len(message)), message)
        )
        return message.encode("ascii")

    async def _fetch_user_id_from_server(self, client: httpx.AsyncClient) -> int:
        while True:
            response = await client.get(
                f"{self._api_endpoint}/v1/user/id?public={self.public_key.hex()}",  # noqa: E501
                timeout=self._register_timeout,
            )
            if response.status_code == 200:
                response_data = response.json()
                if "id" in response_data:
                    return int(response_data["id"])
            await asyncio.sleep(0.1)

    def _create_signed_order_transaction(self, order: PlaceOrderRequest) -> bytes:
        assert self.nonce is not None

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

        transaction_data += pack(">II", epoch, self.nonce) + pack(">Q", self.user_id)

        message = (
            "v: 1\n"
            f"name: {order.side.lower()}\n"
            f"base token: {order.base_token}\n"
            f"quote token: {order.quote_token}\n"
            f"amount: {order.volume:g}\n"
            f"price: {order.price}\n"
            f"t: {epoch}\n"
            f"nonce: {self.nonce}\n"
            f"user_id: {self.user_id}\n"
        )
        message = "\x19Ethereum Signed Message:\n" + str(len(message)) + message

        signature = self._private_key.sign_recoverable(
            keccak(message.encode("ascii")), hasher=None
        )
        signature = signature[:64]  # Compact format

        transaction_data += signature
        return transaction_data

    def _create_sigend_cancel_order_transaction(self, signed_order: bytes) -> bytes:
        transaction_data = (
            pack(">B", self._version)
            + pack(">B", self._cancel_command)
            + signed_order[1:-72]
            + pack(">Q", self.user_id)
        )

        message = (
            f"v: {transaction_data[0]}\n"
            "name: cancel\n"
            f"slice: {signed_order[1:-72].hex()}\n"
            f"user_id: {self.user_id}\n"
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

    def _create_signed_withdraw_transaction(
        self, withdraw_request: WithdrawRequest
    ) -> bytes:
        transaction_data = (
            pack(">B", self._version)
            + pack(">B", self._withdraw_command)
            + pack(">B", len(withdraw_request.token_name))
            + withdraw_request.token_chain.encode()
            + withdraw_request.token_name.encode()
            + pack(">d", withdraw_request.amount)
            + bytes.fromhex(withdraw_request.destination[2:])
        )
        epoch = int(time.time())
        transaction_data += (
            pack(">II", epoch, self.nonce) + pack(">Q", self.user_id) + self.public_key
        )

        message = (
            "v: 1\n"
            "name: withdraw\n"
            f"token chain: {withdraw_request.token_chain}\n"
            f"token name: {withdraw_request.token_name}\n"
            f"amount: {withdraw_request.amount}\n"
            f"to: {withdraw_request.destination}\n"
            f"t: {epoch}\n"
            f"nonce: {self.nonce}\n"
            f"user_id: {self.user_id}\n"
            f"public: {self.public_key.hex()}\n"
        )
        message = "\x19Ethereum Signed Message:\n" + str(len(message)) + message

        signature = self._private_key.sign_recoverable(
            keccak(message.encode("ascii")), hasher=None
        )
        signature = signature[:64]  # Compact format

        transaction_data += signature
        return transaction_data

    async def _get_and_parse_response_from_server(
        self,
        type_adapter: TypeAdapter[ServerResponseType],
        api_path: str,
        params: dict[str, Any] | None = None,
    ) -> ServerResponseType:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_endpoint}{api_path}",
                params=params,
            )

        response_data = response.json()
        if response.status_code == 422:
            detail = response_data.get("detail") or []
            raise RuntimeError(
                f"Fetching response from the server failed. Detail: {detail}"
            )

        try:
            return type_adapter.validate_python(response_data)
        except Exception as e:
            raise RuntimeError(f"Parsing response failed with error: {e}") from e
