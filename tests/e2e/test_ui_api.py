"""Test 9: ui-api sanity"""
import time
import httpx
import pytest


def test_uiapi_telemetry(uiapi_url, fastapi_url, alice_token):
    """Test 9: ui-api returns alice's telemetry rows"""
    # Generate some traffic first
    httpx.get(f"{fastapi_url}/items",
              headers={"Authorization": f"Bearer {alice_token}"},
              verify=False, timeout=30)
    httpx.post(f"{fastapi_url}/query",
               headers={"Authorization": f"Bearer {alice_token}"},
               json={"query": "uiapi-test-query"},
               verify=False, timeout=30)

    # Allow telemetry to be ingested
    time.sleep(10)

    deadline = time.time() + 60
    while time.time() < deadline:
        r = httpx.get(
            f"{uiapi_url}/api/telemetry",
            params={"username": "alice"},
            verify=False, timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        if len(data) > 0:
            # Verify all rows belong to alice
            for row in data:
                assert row["username"] == "alice", f"Expected alice, got {row['username']}"
            return
        time.sleep(5)

    pytest.fail("ui-api returned no rows for alice after 60s")


def test_uiapi_health(uiapi_url):
    """ui-api health check"""
    r = httpx.get(f"{uiapi_url}/health", verify=False, timeout=30)
    assert r.status_code == 200


def test_uiapi_users(uiapi_url):
    """ui-api /api/users returns list"""
    r = httpx.get(f"{uiapi_url}/api/users", verify=False, timeout=30)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
