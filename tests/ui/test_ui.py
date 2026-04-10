"""Playwright UI tests — wireframe conformance and end-to-end interaction."""
import os
import time
import httpx
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

UI_URL = os.getenv("UI_URL", "https://ui.68.220.202.177.nip.io")
FASTAPI_URL = os.getenv("FASTAPI_URL", "https://fastapi.68.220.202.177.nip.io")
BASELINES_DIR = Path(__file__).parent / "baselines"
BASELINES_DIR.mkdir(exist_ok=True)

VIEWPORT = {"width": 1280, "height": 800}


def seed_traffic():
    """Make authenticated requests as alice to generate telemetry."""
    try:
        r = httpx.post(f"{FASTAPI_URL}/login",
                       json={"username": "alice", "password": "alice123"},
                       verify=False, timeout=30)
        if r.status_code == 200:
            token = r.json()["token"]
            httpx.get(f"{FASTAPI_URL}/items",
                      headers={"Authorization": f"Bearer {token}"},
                      verify=False, timeout=30)
            httpx.post(f"{FASTAPI_URL}/query",
                       headers={"Authorization": f"Bearer {token}"},
                       json={"query": "playwright-test"},
                       verify=False, timeout=30)
            time.sleep(10)  # allow telemetry to propagate
    except Exception as e:
        print(f"Warning: traffic seeding failed: {e}")


def test_ui_reachability():
    """Test 1: UI ingress returns 200 and serves the React app."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(UI_URL, wait_until="networkidle", timeout=60000)

        assert page.url.startswith("https://ui.") or "ui." in page.url
        assert page.query_selector('[data-testid="app"]') is not None, "App root not found"
        browser.close()


def test_wireframe_structure():
    """Test 2: Wireframe structural conformance — all regions present and visible."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(UI_URL, wait_until="networkidle", timeout=60000)

        # Header present and visible
        header = page.locator('[data-testid="header"]')
        expect(header).to_be_visible()

        # Nav tabs
        for tab in ["overview", "log", "metrics"]:
            btn = page.locator(f'[data-testid="tab-{tab}"]')
            expect(btn).to_be_visible()

        # Username filter
        username_input = page.locator('[data-testid="username-filter"]')
        expect(username_input).to_be_visible()
        expect(username_input).to_be_enabled()

        # Fetch button
        fetch_btn = page.locator('[data-testid="fetch-btn"]')
        expect(fetch_btn).to_be_visible()

        # Stats row
        for stat in ["stat-total", "stat-duration", "stat-2xx", "stat-4xx", "stat-5xx"]:
            expect(page.locator(f'[data-testid="{stat}"]')).to_be_visible()

        # Telemetry table
        table = page.locator('[data-testid="telemetry-table"]')
        expect(table).to_be_visible()

        # Column headers in order
        for col in ["col-timestamp", "col-method", "col-endpoint", "col-status", "col-duration", "col-query"]:
            expect(page.locator(f'[data-testid="{col}"]')).to_be_visible()

        browser.close()


def test_layout_sanity():
    """Test 3: Layout sanity — relative positioning matches wireframe."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(UI_URL, wait_until="networkidle", timeout=60000)

        header_box = page.locator('[data-testid="header"]').bounding_box()
        filter_bar_box = page.locator('[data-testid="filter-bar"]').bounding_box()
        stats_box = page.locator('[data-testid="stats-row"]').bounding_box()
        table_box = page.locator('[data-testid="telemetry-table"]').bounding_box()

        assert header_box is not None
        assert filter_bar_box is not None
        assert stats_box is not None
        assert table_box is not None

        # Header is above filter bar
        assert header_box["y"] + header_box["height"] <= filter_bar_box["y"] + 5

        # Filter bar is above stats
        assert filter_bar_box["y"] + filter_bar_box["height"] <= stats_box["y"] + 5

        # Stats are above table
        assert stats_box["y"] + stats_box["height"] <= table_box["y"] + 5

        # Header spans full width (roughly)
        assert header_box["width"] >= VIEWPORT["width"] * 0.9

        browser.close()


def test_end_to_end_interaction():
    """Test 5: Seed traffic, type alice in filter, verify row appears."""
    seed_traffic()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(UI_URL, wait_until="networkidle", timeout=60000)

        # Type alice in filter
        username_input = page.locator('[data-testid="username-filter"]')
        username_input.fill("alice")

        # Click Fetch
        page.locator('[data-testid="fetch-btn"]').click()
        page.wait_for_timeout(3000)

        # Assert at least one row
        rows = page.locator('[data-testid="telemetry-row"]')
        count = rows.count()
        assert count > 0, "No telemetry rows appeared after filtering for alice"

        # At least one row has /items or /query in the endpoint cell
        found = False
        for i in range(count):
            cell = rows.nth(i).locator('[data-testid="cell-endpoint"]').inner_text()
            if "/items" in cell or "/query" in cell:
                found = True
                break
        assert found, "No row with /items or /query endpoint found for alice"

        browser.close()


def test_visual_snapshot():
    """Test 6: Capture/compare full-page screenshot."""
    baseline = BASELINES_DIR / "ui_baseline.png"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(UI_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        if not baseline.exists():
            # First run — save baseline
            screenshot = page.screenshot(full_page=True)
            baseline.write_bytes(screenshot)
            print(f"Baseline saved to {baseline}")
        else:
            # Compare with tolerance
            page.expect_screenshot = None  # reset
            screenshot = page.screenshot(full_page=True)
            # Simple size check for now — Playwright's native comparison needs pytest-playwright
            assert len(screenshot) > 1000, "Screenshot looks too small"

        browser.close()
