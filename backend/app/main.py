from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db
from app.api.v1 import agents, workflows, executions, templates, health, custom_tools
from app.api.ws import monitor
# Import all models so init_db creates their tables
import app.models.workflow_template  # noqa: F401
import app.models.custom_tool  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Enforce X-API-Key when API_KEY is configured. Skips health, docs, and WebSocket routes."""
    if not settings.API_KEY:
        return await call_next(request)
    skip_prefixes = ("/api/v1/health", "/docs", "/openapi.json", "/redoc", "/ws/", "/")
    if any(request.url.path.startswith(p) for p in skip_prefixes) and request.url.path != "/api/":
        return await call_next(request)
    key = request.headers.get("X-API-Key", "")
    if key != settings.API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


app.include_router(health.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(executions.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(custom_tools.router, prefix="/api/v1")
app.include_router(monitor.router)


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}
