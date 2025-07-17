import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, Self
from unittest.mock import AsyncMock, Mock, patch

import httpx
import websockets

_WEBSOCKET_CLOSE_SENTINEL = object()


@dataclass
class ReceivedRequest:
    path: str
    method: Literal["GET", "POST"]
    body: Any
    params: dict[str, Any] | None = None


class MockZexWebSocket:
    def __init__(
        self,
        server_mock: "MockZexServer",
        on_open_callback: Callable[[Self], Awaitable[None]] | None = None,
    ) -> None:
        self._server_mock = server_mock
        self._on_open_callback = on_open_callback
        self._closed = False
        self.client_sent_messages_to_server: list[str] = []

    @property
    def closed(self) -> bool:
        return self._closed

    async def __aenter__(self) -> Self:
        if (
            self._server_mock._active_websocket
            and self._server_mock._active_websocket is not self
            and not self._server_mock._active_websocket.closed
        ):
            await self._server_mock._active_websocket.close()

        self._server_mock._active_websocket = self
        self._server_mock._ws_to_client_queue = asyncio.Queue()

        if self._on_open_callback:
            await self._on_open_callback(self)
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> str:
        try:
            message = await self.recv()
        except websockets.exceptions.ConnectionClosed:
            raise StopAsyncIteration
        return message

    async def send(self, message: str) -> None:
        if self._closed:
            raise RuntimeError()
        self.client_sent_messages_to_server.append(message)
        if self._server_mock._ws_on_message_from_client_callback:
            await self._server_mock._ws_on_message_from_client_callback(message)

    async def recv(self) -> str:
        if self._closed and (
            self._server_mock._ws_to_client_queue is None
            or self._server_mock._ws_to_client_queue.empty()
        ):
            raise RuntimeError()

        if self._server_mock._ws_to_client_queue is None:
            raise RuntimeError(
                "WebSocket queue not initialized for the active connection."
            )

        message = await self._server_mock._ws_to_client_queue.get()
        if message is _WEBSOCKET_CLOSE_SENTINEL:
            self._closed = True
            if self._server_mock._ws_to_client_queue:
                self._server_mock._ws_to_client_queue.put_nowait(
                    _WEBSOCKET_CLOSE_SENTINEL
                )
            raise RuntimeError()
        if not isinstance(message, str):
            raise TypeError(f"Expected str from queue, got {type(message)}")
        return message

    async def close(self, code: int = 1000, reason: str = "") -> None:
        if not self._closed:
            self._closed = True
            if self._server_mock._ws_to_client_queue:
                await self._server_mock._ws_to_client_queue.put(
                    _WEBSOCKET_CLOSE_SENTINEL
                )
            if self._server_mock._active_websocket is self:
                self._server_mock._active_websocket = None


class MockZexServer:
    def __init__(self) -> None:
        self._httpx_patch_target = "zex.sdk.client.async_client.httpx.AsyncClient"
        self._ws_patch_target = "zex.sdk.websocket.base_socket.websockets.connect"

        self._user_ids: dict[str, int] = {}
        self._nonces: dict[int, int] = {}
        self._next_user_id: int = 1
        self._http_received_requests: list[ReceivedRequest] = []

        self._active_websocket: MockZexWebSocket | None = None
        self._ws_to_client_queue: asyncio.Queue[str | object] | None = None
        self._ws_on_message_from_client_callback: (
            Callable[[str], Awaitable[None]] | None
        ) = None
        self._ws_on_open_callback: (
            Callable[[MockZexWebSocket], Awaitable[None]] | None
        ) = None

        self.mock_httpx_client_instance = AsyncMock(spec=httpx.AsyncClient)
        self.mock_httpx_client_instance.get = AsyncMock(
            side_effect=self._handle_http_get
        )
        self.mock_httpx_client_instance.post = AsyncMock(
            side_effect=self._handle_http_post
        )
        self.mock_httpx_client_instance.__aenter__ = AsyncMock(
            return_value=self.mock_httpx_client_instance
        )
        self.mock_httpx_client_instance.__aexit__ = AsyncMock(return_value=None)

        self._patcher_httpx_async_client = patch(
            self._httpx_patch_target, return_value=self.mock_httpx_client_instance
        )

        self._patcher_websockets_connect = patch(
            self._ws_patch_target, new=self._create_mock_websocket_connection_obj
        )
        self.api_base_url_prefix_for_path_extraction = "/v1"

    @property
    def http_received_requests(self) -> list[ReceivedRequest]:
        return self._http_received_requests

    @property
    def ws_client_sent_messages(self) -> list[str]:
        if self._active_websocket:
            return self._active_websocket.client_sent_messages_to_server
        return []

    def set_websocket_callbacks(
        self,
        on_open: Callable[[MockZexWebSocket], Awaitable[None]] | None = None,
        on_message_from_client: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        self._ws_on_open_callback = on_open
        self._ws_on_message_from_client_callback = on_message_from_client

    async def start(self) -> None:
        self._patcher_httpx_async_client.start()
        self._patcher_websockets_connect.start()

    async def stop(self) -> None:
        self._patcher_httpx_async_client.stop()
        self._patcher_websockets_connect.stop()
        if self._active_websocket:
            await self._active_websocket.close()
        self.clear_state()

    def clear_state(self) -> None:
        self._user_ids.clear()
        self._nonces.clear()
        self._next_user_id = 1
        self._http_received_requests.clear()

        if self._ws_to_client_queue:
            while not self._ws_to_client_queue.empty():
                try:
                    self._ws_to_client_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        self._active_websocket = None

    async def send_to_client_websocket(self, message: str | dict[str, Any]) -> None:
        if (
            self._ws_to_client_queue is None
            or self._active_websocket is None
            or self._active_websocket.closed
        ):
            return

        msg_str: str
        if isinstance(message, dict):
            msg_str = json.dumps(message)
        elif isinstance(message, str):
            msg_str = message
        else:
            raise TypeError("WebSocket message must be str or dict")

        await self._ws_to_client_queue.put(msg_str)

    async def disconnect_client_websocket(self) -> None:
        if self._active_websocket and not self._active_websocket.closed:
            await self._active_websocket.close()

    def set_nonce_for_user(self, user_id: int, nonce: int) -> None:
        self._nonces[user_id] = nonce

    def get_user_id_for_public_key(self, public_key: str) -> int | None:
        return self._user_ids.get(public_key)

    def _get_path_from_url(self, url_str: str) -> str:
        full_path = httpx.URL(url_str).path
        if self.api_base_url_prefix_for_path_extraction and full_path.startswith(
            self.api_base_url_prefix_for_path_extraction
        ):
            return full_path
        return full_path

    async def _handle_http_get(
        self,
        url: str,
        params: dict[str, Any] | None = None,  # noqa: F841
        **kwargs: Any,  # noqa: F841
    ) -> AsyncMock:
        parsed_url = httpx.URL(url)
        path = parsed_url.path
        query_params = dict(parsed_url.params)

        self._http_received_requests.append(
            ReceivedRequest(path=path, method="GET", body=None, params=query_params)
        )

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.headers = httpx.Headers()
        mock_response.request = httpx.Request("GET", url)

        if path.endswith("/user/id"):
            public_key = query_params.get("public")
            if public_key:
                if public_key not in self._user_ids:
                    self._user_ids[public_key] = self._next_user_id
                    self._next_user_id += 1
                user_id = self._user_ids[public_key]
                mock_response.status_code = 200
                mock_response.json = Mock(return_value={"id": user_id})
            else:
                mock_response.status_code = 400
                mock_response.json = Mock(return_value={"error": "Public key required"})
        elif path.endswith("/user/nonce"):
            user_id_str = query_params.get("id")
            if user_id_str:
                user_id = int(user_id_str)
                nonce = self._nonces.get(user_id, 0)
                mock_response.status_code = 200
                mock_response.json = Mock(return_value={"nonce": nonce})
            else:
                mock_response.status_code = 400
                mock_response.json = Mock(return_value={"error": "User ID required"})
        else:
            mock_response.status_code = 404
            mock_response.json = Mock(return_value={"error": "Not Found"})

        return mock_response

    async def _handle_http_post(
        self, url: str, json: Any = None, **kwargs: Any  # noqa: F841
    ) -> AsyncMock:
        parsed_url = httpx.URL(url)
        path = parsed_url.path

        self._http_received_requests.append(
            ReceivedRequest(path=path, method="POST", body=json, params=None)
        )

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.headers = httpx.Headers()
        mock_response.request = httpx.Request("POST", url, json=json)

        if path.endswith("/register"):
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"status": "ok"})
        elif path.endswith("/order"):
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"status": "orders received"})
        else:
            mock_response.status_code = 404
            mock_response.json = Mock(return_value={"error": "Not Found"})

        return mock_response

    def _create_mock_websocket_connection_obj(
        self, uri: str, **kwargs: Any  # noqa: F841
    ) -> MockZexWebSocket:
        new_ws = MockZexWebSocket(self, on_open_callback=self._ws_on_open_callback)
        return new_ws
