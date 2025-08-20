import os

import pytest


@pytest.fixture(scope="session")
def zex_dev_api_key() -> str:
    key = os.getenv("ZEX_DEV_API_KEY")
    if not key:
        pytest.fail("ZEX_DEV_API_KEY environment variable is not set.")
    return key


@pytest.fixture(scope="session")
def zex_main_api_key() -> str:
    key = os.getenv("ZEX_MAIN_API_KEY")
    if not key:
        pytest.fail("ZEX_MAIN_API_KEY environment variable is not set.")
    return key
