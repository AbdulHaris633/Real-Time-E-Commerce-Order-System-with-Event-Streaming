# app/main.py
"""
Real-Time E-Commerce Order System API
======================================
FastAPI application with:
  - REST API for order management
  - Kafka event streaming
  - WebSocket real-time notifications
  - Rate limiting (per-IP, per-user, per-endpoint)
  - Redis caching
  - JWT authentication
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, close_db
from app.services.redis_service import close_redis
from app.services.kafka_producer import flush_producer
from app.routes import orders, webhooks, health, auth

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate Limiter ───────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ── App Lifecycle ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting E-Commerce Order System API...")
    await init_db()
    logger.info("✅ Database ready")
    yield
    logger.info("🛑 Shutting down...")
    flush_producer()
    await close_redis()
    await close_db()
    logger.info("✅ Clean shutdown complete")


# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="E-Commerce Order System API",
    description=(
        "Real-time order processing system with Kafka event streaming, "
        "WebSocket notifications, rate limiting, and Docker containerization."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = settings.app_version
    return response


# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
