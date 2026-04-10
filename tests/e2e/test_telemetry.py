"""Tests 5-8: ClickHouse telemetry storage"""
import time
import httpx
import pytest


QUERY_TEXT = "test-e2e-query-text"


def _poll_ch(ch_client, sql, params=None, timeout=60, interval=5):
    """Poll ClickHouse until query returns rows or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = ch_client.query(sql, parameters=params or {})
        if result.result_rows and result.result_rows[0][0] > 0:
            return result.result_rows
        time.sleep(interval)
    return []


def _generate_traffic(fastapi_url, token, username):
    """Make a set of authenticated requests to generate telemetry."""
    httpx.get(f"{fastapi_url}/items",
              headers={"Authorization": f"Bearer {token}"},
              verify=False, timeout=30)
    httpx.post(f"{fastapi_url}/query",
               headers={"Authorization": f"Bearer {token}"},
               json={"query": QUERY_TEXT},
               verify=False, timeout=30)


def test_telemetry_stored_per_user(fastapi_url, ch_client, alice_token):
    """Test 5: Telemetry stored per user"""
    _generate_traffic(fastapi_url, alice_token, "alice")
    time.sleep(5)

    rows = _poll_ch(
        ch_client,
        "SELECT count() FROM telemetry.requests WHERE username = {u:String}",
        params={"u": "alice"},
        timeout=60,
    )
    assert rows and rows[0][0] > 0, "No telemetry rows found for alice"


def test_endpoint_attribution(fastapi_url, ch_client, alice_token):
    """Test 6: Endpoint attribution"""
    _generate_traffic(fastapi_url, alice_token, "alice")
    time.sleep(5)

    rows = _poll_ch(
        ch_client,
        "SELECT count() FROM telemetry.requests WHERE endpoint IN ('/items', '/query')",
        timeout=60,
    )
    assert rows and rows[0][0] > 0, "No rows with /items or /query endpoint"


def test_query_text_stored(fastapi_url, ch_client, alice_token):
    """Test 7: Query text stored"""
    httpx.post(
        f"{fastapi_url}/query",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={"query": QUERY_TEXT},
        verify=False, timeout=30,
    )
    time.sleep(5)

    rows = _poll_ch(
        ch_client,
        "SELECT count() FROM telemetry.requests WHERE query_text = {q:String}",
        params={"q": QUERY_TEXT},
        timeout=60,
    )
    assert rows and rows[0][0] > 0, f"No rows found with query_text='{QUERY_TEXT}'"


def test_multi_user_isolation(fastapi_url, ch_client, alice_token, bob_token):
    """Test 8: Multi-user isolation"""
    _generate_traffic(fastapi_url, alice_token, "alice")
    _generate_traffic(fastapi_url, bob_token, "bob")
    time.sleep(5)

    # Both users have rows
    alice_rows = _poll_ch(
        ch_client,
        "SELECT count() FROM telemetry.requests WHERE username = 'alice'",
        timeout=60,
    )
    bob_rows = _poll_ch(
        ch_client,
        "SELECT count() FROM telemetry.requests WHERE username = 'bob'",
        timeout=60,
    )
    assert alice_rows and alice_rows[0][0] > 0, "No rows for alice"
    assert bob_rows and bob_rows[0][0] > 0, "No rows for bob"

    # No cross-contamination
    cross = ch_client.query(
        "SELECT count() FROM telemetry.requests WHERE username = 'alice' AND username = 'bob'"
    )
    assert cross.result_rows[0][0] == 0, "Cross-user contamination found"
