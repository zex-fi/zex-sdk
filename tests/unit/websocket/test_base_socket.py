import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock

import pytest

from tests.utils import MockZexServer
from zex.sdk.client import AsyncClient, SigningVisitorDev
from zex.sdk.websocket import BaseSocket, SocketMessage


class MockSocket(BaseSocket):
    def __init__(
        self,
        client: AsyncClient,
        callback: Callable[[SocketMessage], Awaitable[Any]],
        retry_timeout: float = 10,
    ) -> None:
        super().__init__(client, callback, retry_timeout)
        self.received_messages: list[str] = []

    @property
    def stream_name(self) -> str:
        return "MOCK_STREAM"

    def _parse_message(self, message: str) -> SocketMessage | None:
        if message == "invalid":
            return None
        self.received_messages.append(message)
        return SocketMessage()


@pytest.mark.asyncio
async def test_socket_should_receive_messages_sent_from_the_server(
    mock_zex_server: MockZexServer,
) -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    await client.register_user_id()

    socket = MockSocket(client, AsyncMock())
    sent_message = "some-message"

    # Act
    async with socket:
        await mock_zex_server.send_to_client_websocket(message=sent_message)
        await asyncio.sleep(0.1)  # Wait for the next loop to process the message.

    # Assert
    assert len(socket.received_messages) == 1
    assert socket.received_messages[0] == sent_message


@pytest.mark.asyncio
async def test_socket_should_process_messages_sent_from_the_server(
    mock_zex_server: MockZexServer,
) -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    await client.register_user_id()

    callback = AsyncMock()
    socket = MockSocket(client, callback)
    sent_message = "some-message"

    # Act
    async with socket:
        await mock_zex_server.send_to_client_websocket(message=sent_message)
        await mock_zex_server.send_to_client_websocket(message=sent_message)
        await mock_zex_server.send_to_client_websocket(message=sent_message)
        await asyncio.sleep(0.1)  # Wait for the next loop to process the message.

    # Assert
    assert callback.call_count == 3


@pytest.mark.asyncio
async def test_socket_should_retry_on_websocket_error(
    mock_zex_server: MockZexServer,
) -> None:
    # Arrange
    client = AsyncClient(
        signing_visitor=SigningVisitorDev(
            api_key="e68a96346678e8131622d453ed80b6e1a5ccf19f05727f8a4d31281ae6e82458"
        )
    )
    await client.register_user_id()

    callback = AsyncMock(side_effect=Exception())
    socket = MockSocket(client, callback, retry_timeout=0.1)

    # Act
    async with socket:
        await mock_zex_server.send_to_client_websocket(message="some-message")
        await asyncio.sleep(0.2)  # Wait for the next loop to process the message.
        # Assert
        assert socket.running()
