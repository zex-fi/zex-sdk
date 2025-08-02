import os

import pytest


@pytest.fixture(scope="session")
def zex_api_key() -> str:
    key = os.getenv("ZEX_API_KEY")
    if not key:
        pytest.fail("ZEX_API_KEY environment variable is not set.")
    return key
