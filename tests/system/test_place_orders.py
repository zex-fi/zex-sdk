import pytest

from zex.sdk.client import AsyncClient


@pytest.mark.asyncio
async def test_given_valid_api_key_when_client_is_created_then_user_id_is_registered(
    zex_api_key: str,
) -> None:
    # Given: Empty
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

    # Then: Empty
    # No-op with no orders should not fail


@pytest.mark.asyncio
async def test_given_registered_client_when_cancel_empty_signed_order_list_then_nothing_is_cancelled(
    zex_api_key: str,
) -> None:
    # Given: A registered client
    client = await AsyncClient.create(api_key=zex_api_key)

    # When: Cancelling with no signed orders
    await client.cancel_batch_order([])

    # Then: Empty
    # No exception should be raised and the call completes
