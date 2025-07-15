import asyncio
import json
from contextlib import suppress

import websockets
from websockets import ClientConnection

from zex.sdk.clients import AsyncClient


class ZexSocketManager:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client
        self._websocket_endpoint = "ws://api.zex.finance"

        self._websocket_task: asyncio.Task[None] | None = None
        self._websocket_error_message: str | None = None

    async def __enter__(self) -> None:
        await self._client.register_user_id()
        startup_event = asyncio.Event()
        self._websocket_task = asyncio.create_task(
            self._register_and_run_websocket(startup_event)
        )
        try:
            await asyncio.wait_for(startup_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            return

    async def __exit__(self) -> None:
        assert self._websocket_task is not None
        self._websocket_task.cancel()
        with suppress(asyncio.CancelledError):
            await asyncio.gather(self._websocket_task)
        self._websocket_task = None
        self._websocket_error_message = None

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
                await asyncio.sleep(10)

    async def _on_open(self, websocket: ClientConnection) -> None:
        subscribe_message = json.dumps({
            "method": "SUBSCRIBE",
            "params": [f"{self._client.public_key.hex()}@executionReport"],
            "id": 1,
        })
        await websocket.send(subscribe_message)

    async def _on_message(self, message: str) -> None:
        pass
