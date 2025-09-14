import pytest

from zex.sdk.client import AsyncClient, SigningVisitorDev
from zex.sdk.data_types import OrderSide, PlaceOrderRequest


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_register_user_id_assigns_user_id_when_not_registered() -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )

    # Act
    await client.register_user_id()

    # Assert
    assert client.user_id is not None


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_register_user_id_skips_registration_if_user_id_exists() -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    client.user_id = 1234

    # Act
    await client.register_user_id()

    # Assert
    assert client.user_id == 1234


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_place_batch_order_should_increment_nonce_by_the_number_or_orders() -> (
    None
):
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.1,
        price=30000.0,
        side=OrderSide.BUY,
    )

    # Act
    await client.register_user_id()
    nonce_before_placing_order = client.nonce
    await client.place_batch_order(orders=[order, order, order])
    nonce_after_placing_order = client.nonce

    # Assert
    assert nonce_before_placing_order is None
    assert nonce_after_placing_order == 3


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_place_batch_order_raises_if_not_registered() -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.1,
        price=30000.0,
        side=OrderSide.SELL,
    )

    # Act, Assert
    with pytest.raises(RuntimeError, match="The Zex client is not registered."):
        await client.place_batch_order([order])


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_place_batch_order_returns_without_orders_and_not_query_the_nonce() -> (
    None
):
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )

    # Act
    client.user_id = 1
    await client.place_batch_order([])  # Should silently succeed

    # Assert
    assert client.nonce is None


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_place_batch_order_should_return_the_same_number_of_place_order_results_as_requests() -> (
    None
):
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.1,
        price=30000.0,
        side=OrderSide.SELL,
    )

    # Act
    await client.register_user_id()
    place_order_results = await client.place_batch_order([order, order, order, order])

    # Assert
    assert len(list(place_order_results)) == 4


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_all_place_order_requests_should_be_included_in_place_order_results() -> (
    None
):
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    first_order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.1,
        price=30000.0,
        side=OrderSide.SELL,
    )
    second_order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.01,
        price=30000.0,
        side=OrderSide.SELL,
    )
    third_order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.001,
        price=30000.0,
        side=OrderSide.BUY,
    )

    # Act
    await client.register_user_id()
    place_order_results = await client.place_batch_order(
        [first_order, second_order, third_order]
    )
    place_order_requests_extracted_from_results = [
        result.place_order_request for result in place_order_results
    ]

    # Assert
    assert first_order in place_order_requests_extracted_from_results
    assert second_order in place_order_requests_extracted_from_results
    assert third_order in place_order_requests_extracted_from_results


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_place_order_requests_extracted_from_result_should_preserver_the_same_order() -> (
    None
):
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    first_order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.1,
        price=30000.0,
        side=OrderSide.SELL,
    )
    second_order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.01,
        price=30000.0,
        side=OrderSide.SELL,
    )
    third_order = PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        volume=0.001,
        price=30000.0,
        side=OrderSide.BUY,
    )

    # Act
    await client.register_user_id()
    place_order_results = await client.place_batch_order(
        [first_order, second_order, third_order]
    )
    place_order_results = list(place_order_results)

    # Assert
    assert place_order_results[0].place_order_request == first_order
    assert place_order_results[1].place_order_request == second_order
    assert place_order_results[2].place_order_request == third_order


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_cancel_batch_order_returns_without_payload() -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )

    # Act
    client.user_id = 1
    await client.cancel_batch_order([])  # Should silently succeed

    # Assert
    assert client.nonce is None


@pytest.mark.usefixtures("mock_zex_server")
@pytest.mark.asyncio
async def test_create_classmethod_returns_registered_client() -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )

    # Act
    await client.register_user_id()

    # Assert
    assert isinstance(client, AsyncClient)
    assert client.user_id is not None
