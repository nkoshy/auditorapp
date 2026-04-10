-- Create telemetry database
CREATE DATABASE IF NOT EXISTS telemetry;

-- Create otel database (used by collector)
CREATE DATABASE IF NOT EXISTS otel;

-- Create the primary requests table
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
  attributes     String
) ENGINE = MergeTree
ORDER BY (event_time, username, endpoint);

-- Create the otel_traces table that the collector writes to
CREATE TABLE IF NOT EXISTS otel.otel_traces (
    Timestamp DateTime64(9) CODEC(Delta, ZSTD(1)),
    TraceId String CODEC(ZSTD(1)),
    SpanId String CODEC(ZSTD(1)),
    ParentSpanId String CODEC(ZSTD(1)),
    TraceState String CODEC(ZSTD(1)),
    SpanName LowCardinality(String) CODEC(ZSTD(1)),
    SpanKind LowCardinality(String) CODEC(ZSTD(1)),
    ServiceName LowCardinality(String) CODEC(ZSTD(1)),
    ResourceAttributes Map(LowCardinality(String), String) CODEC(ZSTD(1)),
    ScopeName String CODEC(ZSTD(1)),
    ScopeVersion String CODEC(ZSTD(1)),
    SpanAttributes Map(LowCardinality(String), String) CODEC(ZSTD(1)),
    Duration UInt64 CODEC(ZSTD(1)),
    StatusCode LowCardinality(String) CODEC(ZSTD(1)),
    StatusMessage String CODEC(ZSTD(1)),
    Events Nested (
        Timestamp DateTime64(9),
        Name LowCardinality(String),
        Attributes Map(LowCardinality(String), String)
    ) CODEC(ZSTD(1)),
    Links Nested (
        TraceId String,
        SpanId String,
        TraceState String,
        Attributes Map(LowCardinality(String), String)
    ) CODEC(ZSTD(1))
) ENGINE MergeTree()
PARTITION BY toDate(Timestamp)
ORDER BY (ServiceName, SpanName, toUnixTimestamp(Timestamp), TraceId)
TTL toDateTime(Timestamp) + toIntervalDay(3);

-- Materialized view to project otel_traces into telemetry.requests
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry.requests_mv TO telemetry.requests AS
SELECT
    Timestamp AS event_time,
    TraceId AS trace_id,
    SpanId AS span_id,
    ifNull(SpanAttributes['user.name'], '') AS username,
    ifNull(SpanAttributes['client.ip'], '') AS ip_address,
    ifNull(SpanAttributes['http.target'], SpanName) AS endpoint,
    ifNull(SpanAttributes['http.method'], '') AS method,
    toUInt16OrZero(ifNull(SpanAttributes['http.status_code'], '0')) AS status_code,
    toFloat64OrZero(ifNull(SpanAttributes['http.duration_ms'], '0')) AS duration_ms,
    ifNull(SpanAttributes['query.text'], '') AS query_text,
    toString(SpanAttributes) AS attributes
FROM otel.otel_traces
WHERE SpanAttributes['http.method'] != '';
