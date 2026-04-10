# Test Cases

## 1. Health Check
**Endpoint:** `GET /health`
**Expected:** HTTP 200, `{"status": "ok"}`

## 2. Login Success
**Endpoint:** `POST /login`
**Payload:** `{"username": "alice", "password": "alice123"}`
**Expected:** HTTP 200, response contains `token` field (non-empty string)

## 3. Authenticated /items
**Precondition:** Valid bearer token from login
**Endpoint:** `GET /items`
**Headers:** `Authorization: Bearer <token>`
**Expected:** HTTP 200, response contains `items` list

## 4. Authenticated /query
**Precondition:** Valid bearer token from login
**Endpoint:** `POST /query`
**Headers:** `Authorization: Bearer <token>`
**Payload:** `{"query": "SELECT * FROM users"}`
**Expected:** HTTP 200, response contains `result: ok`

## 5. Telemetry Stored Per User
**Precondition:** Calls made as alice (login, items, query)
**Check:** ClickHouse `telemetry.requests` has rows where `username = 'alice'`
**Expected:** At least 1 row found (allow up to 30s for async ingestion)

## 6. Endpoint Attribution
**Precondition:** Calls to /items and /query have been made
**Check:** ClickHouse has rows where `endpoint IN ('/items', '/query')`
**Expected:** Both endpoints appear in telemetry

## 7. Query Text Stored
**Precondition:** POST /query called with `{"query": "test-query-text"}`
**Check:** ClickHouse row for /query endpoint has `query_text = 'test-query-text'`
**Expected:** Exact query text is found in ClickHouse

## 8. Multi-User Isolation
**Precondition:** Calls made as both alice and bob
**Check:** ClickHouse has rows for both; filtering by username returns only that user's rows
**Expected:** alice rows have username=alice only; bob rows have username=bob only

## 9. ui-api Sanity
**Endpoint:** `GET /api/telemetry?username=alice` (via ingress)
**Expected:** HTTP 200, JSON array containing rows with username=alice
