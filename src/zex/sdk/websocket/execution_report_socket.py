import json
from collections.abc import Awaitable, Callable
from typing import Any

from zex.sdk.client import AsyncClient
from zex.sdk.websocket.base_socket import BaseSocket
from zex.sdk.websocket.socket_message import SocketMessage


class ParsedWebSocketOrderMessage(SocketMessage):
    order_id: int
    client_order_id: int
    order_status_raw: str
    side: str
    symbol: str
    price: float
    cumulative_filled_quantity: float
    exchange_message: str


class ExecutionReportSocket(BaseSocket):
    def __init__(
        self,
        client: AsyncClient,
        callback: Callable[[SocketMessage], Awaitable[Any]],
        retry_timeout: float = 10,
    ) -> None:
        BaseSocket.__init__(self, client, callback, retry_timeout)

    @property
    def stream_name(self) -> str:
        return "@executionReport"

    def _parse_message(self, message: str) -> SocketMessage | None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return None

        if not isinstance(data, dict):
            return None

        if "result" in data and data["result"] is None:
            return None

        order_data = data.get("data")
        if not isinstance(order_data, dict):
            return None

        if order_data.get("e") != "executionReport":
            return None

        try:  # noqa: TRY101
            order_id = int(str(order_data.get("i", "")).strip())
            client_order_id = int(str(order_data.get("c", "")).strip())

            order_status_raw = str(order_data.get("X", "UNKNOWN")).strip()
            side = str(order_data.get("S", "UNKNOWN")).strip().upper()
            symbol = str(order_data.get("s", "UNKNOWN")).strip()

            price = float(str(order_data.get("p", "0")).strip())
            cumulative_filled_quantity = float(str(order_data.get("z", "0")).strip())

            exchange_message = str(order_data.get("r", "") or "").strip()
        except (ValueError, TypeError):
            return None

        if (
            not order_id
            or not client_order_id
            or symbol == "UNKNOWN"
            or side == "UNKNOWN"
        ):
            return None

        return ParsedWebSocketOrderMessage(
            order_id=order_id,
            client_order_id=client_order_id,
            order_status_raw=order_status_raw,
            side=side,
            symbol=symbol,
            price=price,
            cumulative_filled_quantity=cumulative_filled_quantity,
            exchange_message=exchange_message,
        )
