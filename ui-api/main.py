import os
import clickhouse_connect
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Telemetry UI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CH_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CH_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_USER = os.getenv("CLICKHOUSE_USER", "telemetry")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "telemetry123")
CH_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "telemetry")


def get_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        port=CH_PORT,
        username=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE,
    )


@app.get("/api/telemetry")
async def get_telemetry(username: str = None, limit: int = 50):
    client = get_client()
    if username:
        result = client.query(
            "SELECT event_time, trace_id, span_id, username, ip_address, endpoint, method, status_code, duration_ms, query_text FROM requests WHERE username = {username:String} ORDER BY event_time DESC LIMIT {limit:UInt32}",
            parameters={"username": username, "limit": limit}
        )
    else:
        result = client.query(
            "SELECT event_time, trace_id, span_id, username, ip_address, endpoint, method, status_code, duration_ms, query_text FROM requests ORDER BY event_time DESC LIMIT {limit:UInt32}",
            parameters={"limit": limit}
        )
    rows = []
    for row in result.result_rows:
        rows.append({
            "event_time": str(row[0]),
            "trace_id": row[1],
            "span_id": row[2],
            "username": row[3],
            "ip_address": row[4],
            "endpoint": row[5],
            "method": row[6],
            "status_code": row[7],
            "duration_ms": row[8],
            "query_text": row[9],
        })
    return rows


@app.get("/api/users")
async def get_users():
    client = get_client()
    result = client.query("SELECT DISTINCT username FROM requests WHERE username != '' ORDER BY username")
    return [row[0] for row in result.result_rows]


@app.get("/api/stats")
async def get_stats(username: str = None):
    client = get_client()
    where = "WHERE username = {username:String}" if username else ""
    params = {"username": username} if username else {}
    result = client.query(
        f"""SELECT
            count() as total,
            avg(duration_ms) as avg_duration,
            countIf(status_code >= 200 AND status_code < 300) as success_2xx,
            countIf(status_code >= 400 AND status_code < 500) as errors_4xx,
            countIf(status_code >= 500) as errors_5xx
        FROM requests {where}""",
        parameters=params
    )
    row = result.result_rows[0] if result.result_rows else (0, 0, 0, 0, 0)
    return {
        "total": row[0],
        "avg_duration_ms": round(float(row[1]), 2) if row[1] else 0,
        "success_2xx": row[2],
        "errors_4xx": row[3],
        "errors_5xx": row[4],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
