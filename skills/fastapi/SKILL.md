---
name: fastapi-production
description: "Production-depth skill for building robust FastAPI services. Use when asked to: add JWT authentication with token refresh to a FastAPI app, implement rate limiting or throttling on API endpoints, set up global exception handlers and structured error responses, configure database connection pooling with SQLAlchemy async sessions, handle 422 validation errors with custom messages, protect endpoints with OAuth2 or API key security schemes, manage async background tasks with proper lifecycle hooks, or tune FastAPI for high-concurrency production deployments."
license: Apache-2.0
compatibility:
- python >= 3.9
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [fastapi, python, async, jwt, rate-limiting, sqlalchemy, pydantic, rest-api, production]
---

# FastAPI Production Skill

## Quick Start

```bash
pip install "fastapi[standard]" sqlalchemy asyncpg python-jose[cryptography] passlib[bcrypt] slowapi
```

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: init DB pools, caches, etc.
    yield
    # shutdown: close connections cleanly

app = FastAPI(title="My API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["https://myapp.com"],
    allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health(): return {"status": "ok"}
```

## When to Use
Use this skill when asked to:
- Add JWT login, access token generation, or token refresh endpoints
- Set up global error handlers or structured JSON error responses
- Rate limit or throttle API routes by IP or user identity
- Configure async SQLAlchemy sessions with connection pooling
- Fix 422 Unprocessable Entity errors from Pydantic validation
- Implement OAuth2 password flow or API key authentication
- Handle lifespan events (startup/shutdown) for resource management
- Run FastAPI under Gunicorn + Uvicorn workers for production concurrency
- Override default validation exception responses
- Protect WebSocket routes or APIRouter-scoped endpoints

## Core Patterns

### Pattern 1: Structured Global Exception Handlers (Source: official)

Register handlers on the `app` instance. Return `JSONResponse` with a consistent envelope so clients always parse the same shape.

```python
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# Consistent error envelope
def error_envelope(status_code: int, message: str, detail=None):
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": status_code, "message": message, "detail": detail}},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_envelope(exc.status_code, exc.detail)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # exc.errors() returns a list; format for human readability
    errors = [
        {"field": ".".join(str(l) for l in e["loc"]), "msg": e["msg"]}
        for e in exc.errors()
    ]
    return error_envelope(status.HTTP_422_UNPROCESSABLE_ENTITY, "Validation failed", errors)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak tracebacks to clients in production
    import logging
    logging.exception("Unhandled error on %s", request.url)
    return error_envelope(500, "Internal server error")
```

> **Note:** `RequestValidationError.__str__` output changed between FastAPI versions (see GitHub Issue #12125). Always call `.errors()` — never cast the exception to `str` for the response body.

---

### Pattern 2: JWT Authentication with Token Refresh (Source: official)

```python
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "change-me-use-secrets-manager"   # ← never hardcode in prod
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI()

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_token_pair(subject: str) -> Token:
    return Token(
        access_token=create_token(
            {"sub": subject, "type": "access"},
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        refresh_token=create_token(
            {"sub": subject, "type": "refresh"},
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        ),
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exc
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exc
        return sub
    except JWTError:
        raise credentials_exc

@app.post("/auth/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # Replace with real user lookup + pwd_context.verify()
    if form.username != "admin" or form.password != "secret":
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    return create_token_pair(form.username)

@app.post("/auth/refresh", response_model=Token)
async def refresh(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("wrong token type")
        return create_token_pair(payload["sub"])
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.get("/me")
async def me(user: Annotated[str, Depends(get_current_user)]):
    return {"user": user}
```

---

### Pattern 3: Rate Limiting with SlowAPI (Source: official + community)

`slowapi` wraps `limits` and integrates cleanly with FastAPI's dependency system.

```python
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Key function: swap get_remote_address for authenticated user ID in prod
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/public")
@limiter.limit("60/minute")
async def public_endpoint(request: Request):        # request param is required by slowapi
    return {"data": "ok"}

@app.get("/expensive")
@limiter.limit("5/minute")
async def expensive_endpoint(request: Request):
    return {"data": "computed"}

# Per-user rate limiting using JWT subject
def get_user_id(request: Request) -> str:
    # Extract 'sub' from Bearer token; fall back to IP
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from jose import jwt as _jwt
            payload = _jwt.decode(auth[7:], "change-me", algorithms=["HS256"])
            return payload.get("sub", get_remote_address(request))
        except Exception:
            pass
    return get_remote_address(request)

user_limiter = Limiter(key_func=get_user_id)
# Source: community / # Tested: SharpSkill
```

---

### Pattern 4: Async Database Sessions with Connection Pooling (Source: official)

```python
from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Pool tuning: pool_size = (CPU cores * 2) + 1 is a common baseline
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,          # persistent connections kept open
    max_overflow=20,       # extra connections allowed under burst
    pool_timeout=30,       # seconds to wait before raising PoolTimeout
    pool_recycle=1800,     # recycle connections older than 30 min (prevents stale TCP)
    pool_pre_ping=True,    # check connection liveness before use
    echo=False,            # set True only during development
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

DbDep = Annotated[AsyncSession, Depends(get_db)]

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int, db: DbDep):
    item = await db.get(Item, item_id)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, "Item not found")
    return {"id": item.id, "name": item.name}
```

---

### Pattern 5: APIRouter with Lifespan Merging (Source: community)

Nested router lifespans were silently dropped before FastAPI 0.109+ — use the `lifespan` parameter on both `APIRouter` and `FastAPI` and merge them explicitly as a workaround for older versions.

```python
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI

# Source: community / # Tested: SharpSkill
router = APIRouter(prefix="/v1")

router_started = False  # simulates a connection resource

@asynccontextmanager
async def router_lifespan(app):
    global router_started
    router_started = True
    print("Router resource connected")
    yield
    router_started = False
    print("Router resource disconnected")

@asynccontextmanager
async def app_lifespan(app):
    # Manually invoke sub-lifespans when framework version doesn't merge them
    async with router_lifespan(app):
        yield

app = FastAPI(lifespan=app_lifespan)
app.include_router(router)

@router.get("/status")
async def status():
    return {"router_started": router_started}
```

---

### Pattern 6: WebSocket on APIRouter (Source: community)

WebSocket routes added to `APIRouter` and then included into `FastAPI` return 403 on some versions due to missing scope handling. The fix is to attach directly to `app` or use `add_api_websocket_route`.

```python
from fastapi import APIRouter, FastAPI, WebSocket

# Source: community / # Tested: SharpSkill
app = FastAPI()
router = APIRouter()

# ✅ Works reliably: declare WS routes directly on app
@app.websocket("/ws/direct")
async def ws_direct(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("connected")
    await websocket.close()

# ✅ Alternative: use add_api_websocket_route after include_router
async def ws_handler(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_text()
    await websocket.send_text(f"echo: {data}")
    await websocket.close()

app.include_router(router)
# Register AFTER include_router to avoid 403 scope bug on older FastAPI
app.add_api_websocket_route("/ws/echo", ws_handler)
```

---

## Production Notes

**1. `RequestValidationError.__str__` returns JSON, not human-readable text**
Calling `str(exc)` on a `RequestValidationError` returns raw JSON in FastAPI ≥ 0.100 with Pydantic v2. Documentation examples expecting `"1 validation error\npath -> field"` format will break. Always use `.errors()` and format the list yourself.
Source: GitHub Issues #12125

**2. Context managers in `Depends` broken after 0.106**
Generator-based dependencies that use `yield` with internal `async with` blocks can behave incorrectly after FastAPI 0.106 due to exception propagation changes in dependency teardown. Pin to 0.109.1+ where this is resolved, or restructure to explicit try/finally.
Source: GitHub Issues #11107

**3. Nested router lifespans silently ignored**
`app.include_router(router)` does not automatically merge `lifespan` context managers defined on the router. Resources opened in a router's lifespan never start unless explicitly composed into the app's lifespan.
Source: GitHub Issues (🐛 Ensure that `app.include_router` merges nested lifespans)

**4. `APIKeyHeader` scheme name collision**
When registering multiple `APIKeyHeader` instances, they all default to the same OpenAPI security scheme name, causing one to overwrite the other in the generated docs. Pass a unique `scheme_name` argument to each instance.
Source: GitHub Issues (🐛 fix APIKey scheme name default)

**5. `HTTPDigest` always raises 401 even with `auto_error=False`**
Unlike `HTTPBearer` and `HTTPBasic`, the `HTTPDigest` security dependency ignores `auto_error=False` and raises unconditionally. Workaround: write a custom dependency that checks the header manually and returns `None` when absent.
Source: GitHub Issues (🐛 Ensure that `HTTPDigest` only raises exception when `auto_error is True`)

---

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `422 Unprocessable Entity` on POST with valid JSON | Body sent as `form` content-type or missing `Content-Type: application/json` header | Set `Content-Type: application/json`; use `dict` body or proper Pydantic model |
| WebSocket returns `403 Forbidden` | WS route declared on `APIRouter` before `include_router` — scope middleware not applied | Declare WS directly on `app` or use `app.add_api_websocket_route` after `include_router` |
| `Error loading ASGI app.