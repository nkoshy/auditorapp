import os
import time
import pytest
import httpx
import clickhouse_connect

FASTAPI_URL = os.getenv("FASTAPI_URL", "https://fastapi.68.220.202.177.nip.io")
UIAPI_URL = os.getenv("UIAPI_URL", "https://uiapi.68.220.202.177.nip.io")
CH_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CH_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_USER = os.getenv("CLICKHOUSE_USER", "telemetry")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "telemetry123")


def wait_for_service(url, timeout=120, interval=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{url}/health", timeout=10, verify=False)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(f"Service {url} not ready after {timeout}s")


def wait_for_clickhouse(timeout=120, interval=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            client = clickhouse_connect.get_client(
                host=CH_HOST, port=CH_PORT,
                username=CH_USER, password=CH_PASSWORD,
            )
            client.query("SELECT 1")
            return client
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(f"ClickHouse not ready after {timeout}s")


@pytest.fixture(scope="session")
def fastapi_url():
    wait_for_service(FASTAPI_URL)
    return FASTAPI_URL


@pytest.fixture(scope="session")
def uiapi_url():
    wait_for_service(UIAPI_URL)
    return UIAPI_URL


@pytest.fixture(scope="session")
def ch_client():
    return wait_for_clickhouse()


@pytest.fixture(scope="session")
def alice_token(fastapi_url):
    r = httpx.post(f"{fastapi_url}/login",
                   json={"username": "alice", "password": "alice123"},
                   verify=False, timeout=30)
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture(scope="session")
def bob_token(fastapi_url):
    r = httpx.post(f"{fastapi_url}/login",
                   json={"username": "bob", "password": "bob123"},
                   verify=False, timeout=30)
    assert r.status_code == 200
    return r.json()["token"]
