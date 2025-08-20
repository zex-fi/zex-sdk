import asyncio

import pytest

from zex.sdk.client import AsyncClient
from zex.sdk.data_types import OrderSide, PlaceOrderRequest
from zex.sdk.websocket import ParsedWebSocketOrderMessage, ZexSocketManager


@pytest.mark.asyncio
async def test_given_valid_api_key_when_client_is_created_then_user_id_is_registered(
    zex_api_key: str,
) -> None:
    # Given (Empty)  # noqa: E800
    # When: Creating a client
    client = await AsyncClient.create(api_key=zex_api_key)

    # Then: The user_id should be registered and not None
    assert client.user_id is not None


@pytest.mark.asyncio
async def test_given_registered_client_when_place_empty_order_list_then_nothing_is_submitted(
    zex_api_key: str,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_api_key)

    # When: Placing a batch with no orders
    await client.place_batch_order([])

    # Then (Empty)  # noqa: E800
    # No-op with no orders should not fail


@pytest.mark.asyncio
async def test_given_registered_client_when_cancel_empty_signed_order_list_then_nothing_is_cancelled(
    zex_api_key: str,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_api_key)

    # When: Cancelling with no signed orders
    await client.cancel_batch_order([])

    # Then (Empty)  # noqa: E800
    # No exception should be raised and the call completes


@pytest.mark.asyncio
async def test_given_registered_client_when_place_order_then_new_status_order_message_arrives_from_websocket(
    zex_api_key: str,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_api_key, testnet=False)
    socket_manager = ZexSocketManager(client)
    order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="zUSDT",
        side=OrderSide.BUY,
        volume=0.0001,
        price=30000.0,
    )

    updated_order_status = []

    async def extract_new_order_status(
        order_update_message: ParsedWebSocketOrderMessage,
    ) -> None:
        updated_order_status.append(order_update_message.order_status_raw)

    # When: Placing a batch with one order
    execution_report_socket = await socket_manager.execution_report_socket(
        callback=extract_new_order_status
    )
    async with execution_report_socket:
        await client.place_batch_order([order])
        await asyncio.sleep(2)

    status = updated_order_status.pop()

    # Then: New order status should arrive
    assert status == "NEW"


@pytest.mark.parametrize(
    "base_token, quote_token, side, volume, price",
    [
        # NOTE: The prices are too high/low so they won't get filled.
        ("BTC", "zUSDT", OrderSide.BUY, 0.0001, 30000.0),  # Regular BTC buy.
        ("BTC", "zUSDT", OrderSide.SELL, 0.0001, 300000.0),  # Regular BTC sell.
        ("ETH", "zUSDT", OrderSide.BUY, 0.0001, 3000.0),  # Regular ETH buy.
        ("ETH", "zUSDT", OrderSide.SELL, 0.0001, 300000.0),  # Regular ETH sell.
        ("BTC", "zUSDT", OrderSide.BUY, 0.00001, 30000.0),  # 5 decimal digit volume.
        ("BTC", "zUSDT", OrderSide.BUY, 0.000001, 30000.0),  # 6 decimal digit volume.
        ("BTC", "zUSDT", OrderSide.BUY, 0.0000001, 30000.0),  # 7 decimal digit volume.
        ("BTC", "zUSDT", OrderSide.BUY, 0.000171, 30000.0),  # 6 Non-zero decimals.
        ("BTC", "zUSDT", OrderSide.BUY, 0.0001711, 30000.0),  # 7 Non-zero decimals.
        ("BTC", "zUSDT", OrderSide.BUY, 0.00017112, 30000.0),  # 8 Non-zero decimals.
        ("BTC", "zUSDT", OrderSide.BUY, 0.000171123, 30000.0),  # 9 Non-zero decimals.
        ("BTC", "zUSDT", OrderSide.BUY, 0.0001711231, 30000.0),  # 10 Non-zero decimals.
        ("BTC", "zUSDT", OrderSide.BUY, 0.00017112312, 30000.0),  # 11 Non-zero decimals.
        ("BTC", "zUSDT", OrderSide.BUY, 0.000171123129, 30000.0),  # 12 Non-zero decimals.
        ("BTC", "zUSDT", OrderSide.BUY, 0.0001711231241, 30000.0),  # 13 Non-zero decimals.
        ("ETH", "zUSDT", OrderSide.SELL, 0.000171123, 300000.0),  # Non-zero decimals ETH.
        ("ETH", "zUSDT", OrderSide.SELL, 0.000171120, 300000.0),  # With leading zero.
    ],
)
@pytest.mark.asyncio
async def test_given_registered_client_when_cancel_order_then_cancel_status_order_message_arrives_from_websocket(
    base_token: str,
    quote_token: str,
    side: OrderSide,
    volume: float,
    price: float,
    zex_api_key: str,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_api_key, testnet=False)
    socket_manager = ZexSocketManager(client)
    order = PlaceOrderRequest(
        base_token=base_token,
        quote_token=quote_token,
        side=side,
        volume=volume,
        price=price,
    )

    updated_order_status = []

    async def extract_new_order_status(
        order_update_message: ParsedWebSocketOrderMessage,
    ) -> None:
        updated_order_status.append(order_update_message.order_status_raw)

    # When: Placing a batch with one order and canceling that same batch
    execution_report_socket = await socket_manager.execution_report_socket(
        callback=extract_new_order_status
    )
    async with execution_report_socket:
        place_order_results = await client.place_batch_order([order])
        await asyncio.sleep(2)
        await client.cancel_batch_order(
            place_order_result.signed_order_transaction
            for place_order_result in place_order_results
        )
        await asyncio.sleep(2)

    first_status = updated_order_status[0]
    second_status = updated_order_status[1]

    # Then: New order status should arrive
    assert first_status == "NEW"
    assert second_status == "CANCELED"
