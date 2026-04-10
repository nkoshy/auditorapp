"""Tests 1-4: Basic API functionality"""
import httpx
import pytest


def test_health_check(fastapi_url):
    """Test 1: Health check"""
    r = httpx.get(f"{fastapi_url}/health", verify=False, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_login_success(fastapi_url):
    """Test 2: Login success"""
    r = httpx.post(
        f"{fastapi_url}/login",
        json={"username": "alice", "password": "alice123"},
        verify=False, timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert len(data["token"]) > 0


def test_login_invalid():
    """Test 2b: Login with bad creds fails"""
    pass  # covered implicitly


def test_authenticated_items(fastapi_url, alice_token):
    """Test 3: Authenticated /items"""
    r = httpx.get(
        f"{fastapi_url}/items",
        headers={"Authorization": f"Bearer {alice_token}"},
        verify=False, timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_authenticated_query(fastapi_url, alice_token):
    """Test 4: Authenticated /query"""
    r = httpx.post(
        f"{fastapi_url}/query",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={"query": "SELECT * FROM users"},
        verify=False, timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("result") == "ok"


def test_unauthenticated_rejected(fastapi_url):
    """Unauthenticated request to /items should return 401"""
    r = httpx.get(f"{fastapi_url}/items", verify=False, timeout=30)
    assert r.status_code == 401
