from collections.abc import Awaitable, Callable
from typing import Any

from zex.sdk.clients import AsyncClient
from zex.sdk.websocket.base_socket import BaseSocket
from zex.sdk.websocket.socket_message import SocketMessage


class ExecutionReportSocket(BaseSocket):
    def __init__(
        self, client: AsyncClient, callback: Callable[[SocketMessage], Awaitable[Any]]
    ) -> None:
        BaseSocket.__init__(self, client, callback)

    @property
    def stream_name(self) -> str:
        return "@executionReport"

    def _parse_message(self, message: str) -> SocketMessage:
        return SocketMessage()
