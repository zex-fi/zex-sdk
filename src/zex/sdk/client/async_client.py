from __future__ import annotations

import asyncio
from collections.abc import Iterable
from enum import Enum
from typing import Any, TypeVar

import httpx
from pydantic import TypeAdapter

from zex.sdk.client.signing_visitor import SigningVisitor
from zex.sdk.client.signing_visitor_dev import SigningVisitorDev
from zex.sdk.client.signing_visitor_main import SigningVisitorMain
from zex.sdk.data_types import (
    Asset,
    CancelOrderRequest,
    Order,
    PlaceOrderRequest,
    PlaceOrderResult,
    TradeInfo,
    Transfer,
    Withdraw,
    WithdrawRequest,
)

ServerResponseType = TypeVar("ServerResponseType")


class SignatureType(Enum):
    SECP256K1 = 1
    ED25519 = 2


class AsyncClient:
    """
    The asynchronous client of Zex exchange supporting the main functionalities \
    of the exchange API.
    """

    def __init__(
        self,
        signing_visitor: SigningVisitor,
        testnet: bool = True,
    ) -> None:
        self._signing_visitor = signing_visitor
        self._api_endpoint = (
            "https://api-dev.zex.finance" if testnet else "https://api.zex.finance"
        )
        self._version = 1
        self.testnet = testnet

        self._register_timeout = 20.0
        self.nonce: int | None = None
        self.user_id: int | None = None

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
        signing_visitor: SigningVisitor
        if testnet:
            signing_visitor = SigningVisitorDev(api_key=api_key)
        else:
            signing_visitor = SigningVisitorMain(api_key=api_key)
        client = cls(signing_visitor, testnet)
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

        transaction_data = self._signing_visitor.create_register_transaction()

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
            signed_order_transaction = (
                self._signing_visitor.create_place_order_transaction(
                    order, self.nonce, self.user_id
                )
            )
            place_order_results.append(
                PlaceOrderResult(
                    place_order_request=order,
                    nonce=self.nonce,
                    signed_order_transaction=signed_order_transaction,
                )
            )
            self.nonce += 1
            payload.append(signed_order_transaction.decode("latin-1"))

        if not payload:
            return []

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_endpoint}/v1/order",
                json=payload,
            )

        return place_order_results

    async def cancel_batch_order(
        self, cancel_orders: Iterable[CancelOrderRequest]
    ) -> None:
        """
        Cancel a batch of orders in Zex exchange.

        .. note:
            The client should be registered before calling this method.

        :param cancel_orders: The batch cancel order requests.
        """
        if self.user_id is None:
            raise RuntimeError("The Zex client is not registered.")

        payload = []
        for order in cancel_orders:
            cancel_order_transaction = (
                self._signing_visitor.create_cancel_order_transaction(
                    order, self.user_id
                )
            )
            payload.append(cancel_order_transaction.decode("latin-1"))
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

        signed_withdraw_transaction = self._signing_visitor.create_withdraw_transaction(
            withdraw_request, self.nonce, self.user_id
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

    async def _fetch_user_id_from_server(self, client: httpx.AsyncClient) -> int:
        while True:
            response = await client.get(
                f"{self._api_endpoint}/v1/user/id?public={self._signing_visitor.public_key.hex()}",  # noqa: E501
                timeout=self._register_timeout,
            )
            if response.status_code == 200:
                response_data = response.json()
                if "id" in response_data:
                    return int(response_data["id"])
            await asyncio.sleep(0.1)

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
