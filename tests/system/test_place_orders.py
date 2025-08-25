import asyncio

import pytest

from zex.sdk.client import AsyncClient
from zex.sdk.data_types import OrderSide, PlaceOrderRequest
from zex.sdk.websocket import ParsedWebSocketOrderMessage, ZexSocketManager


@pytest.mark.asyncio
async def test_given_valid_api_key_when_client_is_created_then_user_id_is_registered(
    zex_dev_api_key: str,
) -> None:
    # Given (Empty)  # noqa: E800
    # When: Creating a client
    client = await AsyncClient.create(api_key=zex_dev_api_key)

    # Then: The user_id should be registered and not None
    assert client.user_id is not None


@pytest.mark.asyncio
async def test_given_registered_client_when_place_empty_order_list_then_nothing_is_submitted(
    zex_dev_api_key: str,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_dev_api_key)

    # When: Placing a batch with no orders
    await client.place_batch_order([])

    # Then (Empty)  # noqa: E800
    # No-op with no orders should not fail


@pytest.mark.asyncio
async def test_given_registered_client_when_cancel_empty_signed_order_list_then_nothing_is_cancelled(
    zex_dev_api_key: str,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_dev_api_key)

    # When: Cancelling with no signed orders
    await client.cancel_batch_order([])

    # Then (Empty)  # noqa: E800
    # No exception should be raised and the call completes


@pytest.mark.parametrize(
    ("base_token", "quote_token", "side", "volume", "price", "zex_api_key", "testnet"),
    [
        # NOTE: The prices are too high/low so they won't get filled.
        # Dev version.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.0001,
            30000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Regular BTC buy.
        (
            "BTC",
            "zUSDT",
            OrderSide.SELL,
            0.0001,
            300000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Regular BTC sell.
        (
            "ETH",
            "zUSDT",
            OrderSide.BUY,
            0.0001,
            3000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Regular ETH buy.
        (
            "ETH",
            "zUSDT",
            OrderSide.SELL,
            0.0001,
            300000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Regular ETH sell.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.00001,
            30000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # 5 decimal digit volume.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.000171,
            30000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # 6 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.0001711,
            30000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # 7 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.00017112,
            30000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # 8 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.000171123,
            30000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # 9 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.0001711231,
            30000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # 10 Non-zero decimals.
        (
            "ETH",
            "zUSDT",
            OrderSide.SELL,
            0.000171123,
            300000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Non-zero decimals ETH.
        (
            "ETH",
            "zUSDT",
            OrderSide.SELL,
            0.000171120,
            300000.0,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # With leading zero.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Integer price.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.01,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Price with 2 digits.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.10,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Price Digits leading Zero.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.1123,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Price with 4 digits.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.0001,
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),  # Price with small digits.
        # Main version.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.0001,
            30000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Regular BTC buy.
        (
            "BTC",
            "zUSDT",
            OrderSide.SELL,
            0.0001,
            300000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Regular BTC sell.
        (
            "ETH",
            "zUSDT",
            OrderSide.BUY,
            0.0001,
            3000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Regular ETH buy.
        (
            "ETH",
            "zUSDT",
            OrderSide.SELL,
            0.0001,
            300000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Regular ETH sell.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.00001,
            30000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # 5 decimal digit volume.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.000171,
            30000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # 6 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.0001711,
            30000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # 7 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.00017112,
            30000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # 8 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.000171123,
            30000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # 9 Non-zero decimals.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.0001711231,
            30000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # 10 Non-zero decimals.
        (
            "ETH",
            "zUSDT",
            OrderSide.SELL,
            0.000171123,
            300000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Non-zero decimals ETH.
        (
            "ETH",
            "zUSDT",
            OrderSide.SELL,
            0.000171120,
            300000.0,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # With leading zero.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Integer price.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.01,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Price with 2 digits.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.10,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Price Digits leading Zero.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.1123,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Price with 4 digits.
        (
            "BTC",
            "zUSDT",
            OrderSide.BUY,
            0.001,
            30000.0001,
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),  # Price with small digits.
    ],
)
@pytest.mark.asyncio
async def test_given_registered_client_when_place_and_cancel_orders_then_feedbacks_should_be_receievd_via_websocket(
    base_token: str,
    quote_token: str,
    side: OrderSide,
    volume: float,
    price: float,
    zex_api_key: str,
    testnet: bool,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_api_key, testnet=testnet)
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


@pytest.mark.parametrize(
    ("zex_api_key", "testnet"),
    [
        (
            pytest.lazy_fixture("zex_main_api_key"),  # type: ignore
            False,
        ),
        (
            pytest.lazy_fixture("zex_dev_api_key"),  # type: ignore
            True,
        ),
    ],
)
@pytest.mark.asyncio
async def test_given_a_batch_of_orders_when_place_and_cancel_then_feedbacks_should_be_received_via_websocket(
    zex_api_key: str,
    testnet: bool,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_api_key, testnet=testnet)
    socket_manager = ZexSocketManager(client)
    place_order_requests = [
        PlaceOrderRequest(
            base_token="BTC",
            quote_token="zUSDT",
            side=OrderSide.BUY,
            volume=0.0001,
            price=30000,
        ),
        PlaceOrderRequest(
            base_token="BTC",
            quote_token="zUSDT",
            side=OrderSide.BUY,
            volume=0.0001,
            price=31000,
        ),
        PlaceOrderRequest(
            base_token="BTC",
            quote_token="zUSDT",
            side=OrderSide.BUY,
            volume=0.0001,
            price=32000,
        ),
        PlaceOrderRequest(
            base_token="BTC",
            quote_token="zUSDT",
            side=OrderSide.BUY,
            volume=0.0001,
            price=33000,
        ),
    ]

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
        place_order_results = await client.place_batch_order(place_order_requests)
        await asyncio.sleep(2)
        await client.cancel_batch_order(
            place_order_result.signed_order_transaction
            for place_order_result in place_order_results
        )
        await asyncio.sleep(2)

    first_status = updated_order_status[0]
    second_status = updated_order_status[1]
    third_status = updated_order_status[2]
    fourth_status = updated_order_status[3]
    fifth_status = updated_order_status[4]
    sixth_status = updated_order_status[5]
    seventh_status = updated_order_status[6]
    eighth_status = updated_order_status[7]

    # Then: New order status should arrive
    assert first_status == "NEW"
    assert second_status == "NEW"
    assert third_status == "NEW"
    assert fourth_status == "NEW"
    assert fifth_status == "CANCELED"
    assert sixth_status == "CANCELED"
    assert seventh_status == "CANCELED"
    assert eighth_status == "CANCELED"
