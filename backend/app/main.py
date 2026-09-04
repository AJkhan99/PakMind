"""PakMind — Unified FastAPI backend.

Single FastAPI app serving PakGuide, PakWatch, and PakScholar modules.

Security features:
- Configurable CORS (from ALLOWED_ORIGINS env var)
- IP-based rate limiting on POST endpoints
- Request size limits
- Security headers
- Unified health check endpoint
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PakMind API",
    description="Unified backend for PakMind — PakGuide, PakWatch, PakScholar",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- Security Middleware ----

settings = get_settings()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

# Trusted host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)


# ---- Rate Limiting ----

class RateLimiter:
    """Simple in-memory IP-based rate limiter."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, ip: str) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - self.window
        self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
        if len(self.requests[ip]) >= self.max_requests:
            retry_after = int(self.requests[ip][0] + self.window - now) + 1
            return False, retry_after
        self.requests[ip].append(now)
        remaining = self.max_requests - len(self.requests[ip])
        return True, remaining


rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60,
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method == "POST" and settings.rate_limit_enabled:
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        allowed, retry_after = rate_limiter.is_allowed(client_ip)
        if not allowed:
            logger.warning("Rate limit exceeded for IP: %s", client_ip)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please wait before sending another query."},
                headers={"Retry-After": str(retry_after)},
            )

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ---- Request size limit ----

@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1_048_576:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Request body too large (max 1MB)."},
        )
    return await call_next(request)


# ---- Mount routers ----

from app.guide.api import router as guide_router
from app.watch.api import router as watch_router
from app.scholar.api import router as scholar_router
from app.shared.feedback_api import router as feedback_router

app.include_router(guide_router, prefix="/api/guide", tags=["guide"])
app.include_router(watch_router, prefix="/api/watch", tags=["watch"])
app.include_router(scholar_router)  # scholar router already has /api/scholar prefix
app.include_router(feedback_router, prefix="/api/feedback", tags=["feedback"])


# ---- Startup ----

@app.on_event("startup")
async def startup_event() -> None:
    missing = settings.validate_required()
    if missing:
        logger.warning(
            "Missing environment variables: %s. "
            "Some features will not work until these are configured.",
            ", ".join(missing),
        )
    else:
        logger.info("PakMind API started — all core credentials configured.")

    # Start PakGuide weekly scheduler
    try:
        from app.guide.scheduler import setup_scheduler
        setup_scheduler()
        logger.info("PakGuide scheduler started.")
    except Exception as exc:
        logger.warning("PakGuide scheduler not started: %s", exc)

    logger.info("CORS origins: %s", settings.get_cors_origins())
    logger.info("Rate limit: %d requests/minute", settings.rate_limit_per_minute)
    logger.info("Modules: PakGuide (/api/guide), PakWatch (/api/watch), PakScholar (/api/scholar)")


# ---- Health Check ----

@app.get("/health")
async def health_check() -> dict:
    missing = settings.validate_required()
    return {
        "status": "healthy" if not missing else "degraded",
        "version": "2.0.0",
        "modules": {
            "guide": {"route": "/api/guide", "status": "active"},
            "watch": {"route": "/api/watch", "status": "active"},
            "scholar": {"route": "/api/scholar", "status": "active"},
        },
        "missing_credentials": missing,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "cors_origins_count": len(settings.get_cors_origins()),
    }


@app.get("/")
async def root() -> dict:
    return {
        "name": "PakMind API",
        "description": "Unified backend for PakMind platform",
        "version": "2.0.0",
        "modules": {
            "guide": "/api/guide",
            "watch": "/api/watch",
            "scholar": "/api/scholar",
            "feedback": "/api/feedback",
        },
        "docs": "/docs",
        "health": "/health",
    }
