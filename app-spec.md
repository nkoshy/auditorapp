# Telemetry Demo System — Build Specification

> Deployment, build, and test-loop rules live in `claude.md` at the repo root. This file defines **what** to build. `claude.md` defines **how** to build, deploy, and iterate. Read both before starting.

## Mission

Build, deploy, and validate a complete telemetry demo system end-to-end, autonomously, without asking the user any questions. Iterate on failures until all acceptance tests pass.

---

## Operating Rules (read first)

1. **No questions to the user.** Make reasonable defaults for anything ambiguous and document them in the final report.
2. **No early stopping.** Do not stop on the first failure. Inspect logs → fix → redeploy → rerun. Repeat until green or until a hard infrastructure limit is hit.
3. **Follow `claude.md`** for all build, deploy, ingress, registry, and test-loop rules.
4. **Hard-block escape hatch only:** If and only if a true infrastructure limitation makes progress impossible, stop and produce a blocking-issue report (format in the Final Report section).
5. **Determinism:** Use fixed test users, fixed test payloads, and retries with timeouts for anything async.

---

## Target Architecture

```
[React UI (nginx pod, ingress)]
          │
          ▼
[ui-api service (ingress)] ──query──► [ClickHouse]
                                          ▲
[FastAPI app (OTel instrumented)] ──► [OTel Collector] ──┘
```

Components to deploy:
- **FastAPI app** — instrumented with OpenTelemetry, emits telemetry per request.
- **OpenTelemetry Collector** — receives OTLP from FastAPI, exports to ClickHouse.
- **ClickHouse** — telemetry backend.
- **ui-api service** — reads telemetry from ClickHouse, filterable by username, exposed via ingress.
- **React UI** — served by nginx pod, exposed via ingress, consumes ui-api.

---

## Execution Loop

Follow the develop → deploy → test → fix cycle defined in `claude.md`. At a high level:

1. **Discover.** Inspect the repo layout and MCP server capabilities.
2. **Implement.** Write application code, instrumentation, collector config, ClickHouse schema, ui-api, React UI, tests.
3. **Deploy.** Build images with kaniko and deploy all components to the `automationx` namespace via the Kubernetes MCP server, per `claude.md`.
4. **Test.** Run `pytest tests/e2e -q` against the deployed stack.
5. **Diagnose on failure.** Pull logs from: FastAPI app, OTel Collector, ClickHouse, ui-api, UI, ingress. Inspect ClickHouse tables directly. Inspect Kubernetes events.
6. **Fix and redeploy.** Patch code/config, rebuild, redeploy, rerun tests.
7. **Repeat** steps 4–6 until all tests pass.

Do not pause between iterations. Do not request approval.

---

## Component Requirements

### 1. FastAPI Application

**Endpoints (minimum):**

| Method | Path | Auth | Behavior |
|---|---|---|---|
| `POST` | `/login` | none | Accepts `{username, password}`, returns `{token}` (bearer). |
| `GET` | `/items` | bearer | Returns a static dummy list. |
| `POST` | `/query` | bearer | Accepts `{query: string}`, returns dummy success result. |
| `GET` | `/health` | none | Returns `{"status":"ok"}`. |

**Auth:** In-memory user store is acceptable. Seed at least two test users (e.g., `alice/alice123`, `bob/bob123`). Issue opaque bearer tokens mapped to usernames in memory. Reject missing/invalid tokens with `401`.

**Structure (suggested):**
```
app/
  main.py
  auth.py
  telemetry.py
  requirements.txt
  Dockerfile
```

### 2. OpenTelemetry Instrumentation

Use the Python OTel SDK + FastAPI auto-instrumentation, plus a middleware that enriches spans with request-specific attributes.

**Every request span must carry these attributes:**
- `timestamp` (from span start)
- `user.name` — authenticated username (or `"anonymous"` for unauth endpoints)
- `http.route` / `http.target` — endpoint path
- `http.method`
- `http.status_code`
- `http.duration_ms`
- `client.ip` (if derivable from headers/socket)
- `operation.name`
- `query.text` — **only** for `POST /query`, the submitted query string
- `trace_id` / `span_id` (native)

Username must be extracted in middleware **after** auth resolution and attached to the current span before the response is returned.

Export via **OTLP/gRPC** to the collector at an env-configurable endpoint (`OTEL_EXPORTER_OTLP_ENDPOINT`).

### 3. OpenTelemetry Collector

- Receivers: OTLP (gRPC + HTTP).
- Processors: `batch`, `memory_limiter`.
- Exporters: ClickHouse exporter (`exporters/clickhouseexporter`) writing traces and logs.
- Config file: `otel-collector-config.yaml`.

Use the contrib distribution image that includes the ClickHouse exporter.

### 4. ClickHouse

Deploy a single-node ClickHouse inside `automationx`. Create a dedicated database `telemetry`.

**Primary table** (either created by the exporter or pre-created by an init job):

```sql
CREATE TABLE IF NOT EXISTS telemetry.requests (
  event_time     DateTime64(3),
  trace_id       String,
  span_id        String,
  username       String,
  ip_address     String,
  endpoint       String,
  method         String,
  status_code    UInt16,
  duration_ms    Float64,
  query_text     String,
  attributes     String  -- JSON blob
) ENGINE = MergeTree
ORDER BY (event_time, username, endpoint);
```

If the ClickHouse exporter writes to its own schema (e.g., `otel_traces`), create a **materialized view** that projects the required fields into `telemetry.requests` so the test suite has a single stable table to query. Document whichever path is chosen.

### 5. ui-api Service

Small FastAPI service exposed via ingress.

Endpoints:
- `GET /api/telemetry?username=<name>&limit=<n>` — returns telemetry rows for that user.
- `GET /api/users` — returns distinct usernames seen in telemetry.
- `GET /health`

Connects to ClickHouse via `clickhouse-connect`. Must return JSON.



### 6. React UI

Minimal React app built and served by an nginx pod, exposed via ingress.

**The UI layout, structure, and visual design MUST match the wireframe provided at `wireframes/` in the repo root.** Before implementing the UI:

1. Read every image file in the `wireframes/` directory.
2. Identify all layout regions (header, sidebar, filters, tables, buttons, footers, etc.), their relative positions, and their labels.
3. Reproduce the structure faithfully: element placement, grouping, ordering, labels, and overall proportions must match the wireframe. Colors and typography may use sensible defaults if not specified in the wireframe, but layout and component hierarchy must match.
4. Do not add UI elements that are not in the wireframe. Do not omit elements that are in the wireframe.

**Functional requirements (must be wired up regardless of wireframe styling):**
- Username filter input.
- Table showing telemetry rows for the selected user (timestamp, endpoint, method, status, duration, query_text).
- Calls ui-api through its ingress URL (configurable at build time or via nginx runtime env substitution).
- No auth on the UI itself.

If any functional requirement above conflicts with the wireframe, prefer the wireframe's layout and adapt the functional element to fit within it.
---

## Deployment

Deploy via the Kubernetes MCP server per the rules in `claude.md`. In particular:

- All resources go into the `automationx` namespace.
- Build images with kaniko in-cluster and push to `registry.68.xxx.xxx.xxx.nip.io` (no credentials required).
- Every public-facing service gets an Ingress on `<app>.68.xxx.xxx.xxx.nip.io` with the `letsencrypt-prod` ClusterIssuer annotation. Reuse existing ingresses for the same hostname to avoid Let's Encrypt rate limits.
- Use these ingress hostnames:
  - **FastAPI app** → `fastapi.68.xxx.xxx.xxx.nip.io`
  - **ui-api** → `uiapi.68.xxx.xxx.xxx.nip.io`
  - **React UI** → `ui.68.xxx.xxx.xxx.nip.io`
- ClickHouse and the OTel Collector are internal-only (ClusterIP services, no ingress).
- Every service must have readiness/liveness probes.
- Generate sensible demo secrets (ClickHouse user/password, etc.) via Kubernetes Secrets.

---

## Test Deliverables

### `tests/test_cases.md`
Human-readable scenarios, one section per test below, with steps and expected outcomes. This is the source of truth for required tests, per `claude.md`.

### `tests/e2e/`
Pytest-style executable tests runnable with:

```
pytest tests/e2e -q
```

Use `httpx` (or `requests`) and `clickhouse-connect`. The suite must:

1. Wait for FastAPI `/health`, ui-api `/health`, and ClickHouse to be reachable (poll with timeout, e.g., 120s).
2. Execute every test below.
3. Use retries with backoff when querying ClickHouse (telemetry ingestion is async; allow up to ~30s per assertion).
4. Exit non-zero on any failure.

Per `claude.md`, the test suite should be packaged into an image and executed from a pod in the `automationx` namespace so it can reach internal services (ClickHouse) directly while hitting FastAPI and ui-api through their ingress URLs.

### Required Test Scenarios

| # | Name | Assertion |
|---|---|---|
| 1 | Health check | `GET /health` → 200 |
| 2 | Login success | `POST /login` with valid creds → 200 + token |
| 3 | Authenticated `/items` | `GET /items` with token → 200 |
| 4 | Authenticated `/query` | `POST /query` with token + payload → 200 |
| 5 | Telemetry stored per user | ClickHouse has rows where `username = <test user>` after calls |
| 6 | Endpoint attribution | Rows exist with `endpoint IN ('/items','/query')` |
| 7 | Query text stored | Row for `/query` has `query_text` matching submitted text |
| 8 | Multi-user isolation | After calls as `alice` and `bob`, ClickHouse has rows for both, and filtering by username returns only that user's rows |
| 9 | ui-api sanity | `GET /api/telemetry?username=alice` via ingress returns JSON containing alice's rows |


### `tests/ui/` — Headless Playwright UI tests

A second test suite using **Playwright for Python** running headless inside a Docker container, executed as a pod in the `automationx` namespace so it can hit the UI through its ingress URL.

**Image:** Base the test image on `mcr.microsoft.com/playwright/python:v1.47.0-jammy` (or current stable) so browsers are preinstalled. Install `pytest` and `pytest-playwright`.

**What the suite must verify:**

1. **Reachability** — The UI ingress (`https://ui.68.xxx.xxx.xxx.nip.io`) returns 200 and serves the React app shell.
2. **Wireframe conformance — structural checks.** For each region identified in the wireframe, assert that a corresponding DOM element exists and is visible. Use stable selectors (`data-testid` attributes added during UI implementation, one per wireframe region). Examples of checks the suite must perform:
   - Header/title region is present and visible.
   - Username filter input exists, is visible, and is interactable.
   - Telemetry table exists with the expected column headers in the expected order (timestamp, endpoint, method, status, duration, query_text — or whatever the wireframe specifies).
   - Any buttons, nav elements, or panels shown in the wireframe exist as DOM nodes with matching labels.
3. **Layout sanity.** Using Playwright's `bounding_box()`, assert relative positioning that the wireframe implies. For example: header is above the table (`header.y + header.height <= table.y`), filter input is above or left-of the table, etc. Keep assertions structural ("A is above B", "A is left-of B", "A spans the full width"), not pixel-exact.
4. **Viewport.** Run tests at a fixed viewport (e.g., 1280x800) so layout assertions are deterministic.
5. **End-to-end interaction.** Seed telemetry by calling the FastAPI app as `alice`, then load the UI, type `alice` into the username filter, trigger the fetch, and assert that at least one row appears in the telemetry table and that the row's endpoint cell contains `/items` or `/query`.
6. **Visual snapshot (baseline).** Capture a full-page screenshot and save it as a test artifact. On first run, store it as the baseline under `tests/ui/baselines/`. On subsequent runs, compare against the baseline using Playwright's `expect(page).to_have_screenshot()` with a reasonable pixel-diff tolerance (e.g., `max_diff_pixel_ratio=0.02`) so minor rendering differences don't cause flakes. A missing baseline on first run is not a failure — generate and commit it.

**Implementation notes for the UI code:**
- Add `data-testid` attributes to every wireframe region so the Playwright tests have stable selectors independent of class names or styling.
- Names should be descriptive: `data-testid="header"`, `data-testid="username-filter"`, `data-testid="telemetry-table"`, `data-testid="telemetry-row"`, etc.

**Run command (inside the test pod):**
```
pytest tests/ui -q
```

**Combined test command for the overall suite (per `claude.md`):**
```
pytest tests/e2e tests/ui -q
```
---

## Repository Layout (target)

```
app/                        # FastAPI telemetry-emitting app
  main.py
  auth.py
  telemetry.py
  requirements.txt
  Dockerfile
ui-api/                     # telemetry read service
  main.py
  requirements.txt
  Dockerfile
ui/                         # React + nginx
  src/
  Dockerfile
  nginx.conf
deploy/                     # k8s manifests
  fastapi.yaml
  ui-api.yaml
  ui.yaml
  otel-collector.yaml
  clickhouse.yaml
  ingress.yaml
otel-collector-config.yaml
clickhouse/
  init.sql
tests/
  test_cases.md
  e2e/
    conftest.py
    test_api.py
    test_telemetry.py
    test_ui_api.py
  Dockerfile                # image used to run the suite in-cluster
claude.md
SPEC.md
```

---

## Acceptance Criteria (all must be true to declare done)

1. FastAPI app, ui-api, and React UI are implemented and deployed to `automationx`.
2. FastAPI is instrumented with OpenTelemetry emitting OTLP.
3. OTel Collector is configured and running, receiving from FastAPI and exporting to ClickHouse.
4. ClickHouse is deployed, reachable inside the namespace, and contains telemetry rows after traffic.
5. Every telemetry row is attributable to the authenticated username (or `anonymous` for unauth).
6. ui-api is reachable via its ingress and filters by username.
7. React UI is reachable via its ingress and renders ui-api data.
8. `tests/test_cases.md` exists and matches the executable suite.
9. `pytest tests/e2e -q` passes end-to-end against the deployed stack, executed from a pod in `automationx`.
10. Deployment rollouts succeeded and ingresses respond over HTTPS with valid Let's Encrypt certs.
11. Any failures encountered during iteration were fixed autonomously.
12. pytest tests/ui -q passes from a Playwright pod in automationx.

---

## Final Report

At the end, output a concise report containing:

- **Implemented:** component-by-component summary.
- **Key file paths.**
- **Deployment:** image tags pushed to the in-cluster registry, manifests applied, ingress URLs for FastAPI, ui-api, and UI.
- **Test results:** each of the 9 tests with pass/fail and timing.
- **Assumptions / defaults chosen** (users, passwords, schema path, image tags, etc.).
- **Iterations performed:** brief log of failures encountered and fixes applied.

### If blocked by a hard limitation
Instead of the success report, produce:

- What was completed.
- Exact blocking issue (component, error, log excerpt).
- What was attempted to resolve it.
- The specific next action that would unblock progress.

---

**Begin immediately. Execute end-to-end. Do not ask the user anything.**
