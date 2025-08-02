from collections.abc import Awaitable, Callable
from typing import Any

from zex.sdk.client import AsyncClient
from zex.sdk.websocket.execution_report_socket import ExecutionReportSocket


class ZexSocketManager:
    """
    The socket manager to create instances and manage sockets for different \
    streams provided by Zex exchange.
    """

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def execution_report_socket(
        self, callback: Callable[[Any], Awaitable[Any]]
    ) -> ExecutionReportSocket:
        """
        Create an instance of the execution report socket to provide live reports \
        of the execution in Zex exchange.

        :param callback: The action taken on each message received by the socket.
        """
        return ExecutionReportSocket(self._client, callback)
