import asyncio
import json
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from contextlib import suppress
from types import TracebackType
from typing import Any

import websockets
from websockets import ClientConnection

from zex.sdk.client import AsyncClient
from zex.sdk.websocket.socket_message import SocketMessage


class BaseSocket:
    def __init__(
        self,
        client: AsyncClient,
        callback: Callable[[SocketMessage], Awaitable[Any]],
        retry_timeout: float = 10,
    ) -> None:
        self._client = client
        self._callback = callback
        self._websocket_endpoint = (
            "wss://api-dev.zex.finance"
            if self._client.testnet
            else "wss://api.zex.finance"
        )
        self._retry_timeout = retry_timeout

        self._websocket_task: asyncio.Task[None] | None = None
        self._websocket_error_message: str | None = None

    @property
    @abstractmethod
    def stream_name(self) -> str:
        pass

    async def __aenter__(self) -> None:
        await self.start()

    async def __aexit__(
        self,
        exc_type: type[BaseException],  # noqa: F841
        exc_value: BaseException,  # noqa: F841
        exc_tb: TracebackType,  # noqa: F841
    ) -> None:
        await self.stop()

    async def start(self) -> None:
        await self._client.register_user_id()
        startup_event = asyncio.Event()
        self._websocket_task = asyncio.create_task(
            self._register_and_run_websocket(startup_event)
        )
        try:
            await asyncio.wait_for(startup_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            return

    async def stop(self) -> None:
        assert self._websocket_task is not None
        self._websocket_task.cancel()
        with suppress(asyncio.CancelledError):
            await asyncio.gather(self._websocket_task)
        self._websocket_task = None
        self._websocket_error_message = None

    def running(self) -> bool:
        return self._websocket_task is not None and not self._websocket_task.done()

    async def _register_and_run_websocket(self, startup_event: asyncio.Event) -> None:
        uri = f"{self._websocket_endpoint}/ws"
        while True:
            try:
                self._websocket_error_message = None
                async with websockets.connect(uri) as websocket:
                    startup_event.set()
                    await self._on_open(websocket)
                    async for message in websocket:
                        await self._on_message(str(message))
            except Exception as e:
                self._websocket_error_message = str(e)
                await asyncio.sleep(self._retry_timeout)

    async def _on_open(self, websocket: ClientConnection) -> None:
        subscribe_message = json.dumps({
            "method": "SUBSCRIBE",
            "params": [f"{self._client.user_id}{self.stream_name}"],
            "id": 1,
        })
        await websocket.send(subscribe_message)

    async def _on_message(self, message: str) -> None:
        parsed_message = self._parse_message(message)
        if parsed_message is None:
            return  # TODO: We may raise the appropriate exception here.
        await self._callback(parsed_message)

    @abstractmethod
    def _parse_message(self, message: str) -> SocketMessage | None:
        pass
