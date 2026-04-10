import os
import pytest
from playwright.sync_api import sync_playwright

UI_URL = os.getenv("UI_URL", "https://ui.68.220.202.177.nip.io")
FASTAPI_URL = os.getenv("FASTAPI_URL", "https://fastapi.68.220.202.177.nip.io")


@pytest.fixture(scope="session")
def ui_url():
    return UI_URL


@pytest.fixture(scope="session")
def fastapi_url():
    return FASTAPI_URL
