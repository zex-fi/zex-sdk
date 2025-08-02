from collections.abc import AsyncIterator

import pytest

from tests.utils import MockZexServer


@pytest.fixture
async def mock_zex_server() -> AsyncIterator[MockZexServer]:
    server = MockZexServer()
    await server.start()
    try:
        yield server
    finally:
        await server.stop()
