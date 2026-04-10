import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from opentelemetry import trace

from auth import authenticate, get_user_from_token
from telemetry import setup_telemetry

app = FastAPI(title="Telemetry Demo App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class QueryRequest(BaseModel):
    query: str


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    user = get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.time()

    # Get span BEFORE call_next — the OTel ASGI instrumentation creates it at
    # the ASGI layer (outside FastAPI's middleware stack), so it is already the
    # current span when our middleware is first entered.  After call_next()
    # returns the span may already be ended (response body flushed), so all
    # attributes that don't depend on the response must be set here.
    span = trace.get_current_span()
    if span and span.is_recording():
        auth_header = request.headers.get("Authorization", "")
        username = "anonymous"
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user = get_user_from_token(token)
            if user:
                username = user

        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

        span.set_attribute("user.name", username)
        span.set_attribute("client.ip", client_ip)
        span.set_attribute("http.route", request.url.path)
        span.set_attribute("http.target", request.url.path)
        span.set_attribute("http.method", request.method)
        span.set_attribute("operation.name", f"{request.method} {request.url.path}")

    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # Best-effort: set response-dependent attributes.  This is a no-op if the
    # span was already ended while flushing the response body, but the ASGI
    # instrumentation already records http.status_code on its own.
    if span and span.is_recording():
        span.set_attribute("http.status_code", response.status_code)
        span.set_attribute("http.duration_ms", round(duration_ms, 2))

    return response


# setup_telemetry must be called AFTER @app.middleware("http") so that
# FastAPIInstrumentor.instrument_app() calls add_middleware() last, making
# OpenTelemetryMiddleware the outermost layer.  Our telemetry_middleware then
# runs inside the OTel span context, so trace.get_current_span() returns a
# recording span before we call call_next().
setup_telemetry(app)


@app.post("/login")
async def login(req: LoginRequest):
    token = authenticate(req.username, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token}


@app.get("/items")
async def get_items(user: str = Depends(get_current_user)):
    return {"items": ["item1", "item2", "item3"], "user": user}


@app.post("/query")
async def run_query(req: QueryRequest, user: str = Depends(get_current_user), request: Request = None):
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("query.text", req.query)
    return {"result": "ok", "query": req.query, "user": user}


@app.get("/health")
async def health():
    return {"status": "ok"}
