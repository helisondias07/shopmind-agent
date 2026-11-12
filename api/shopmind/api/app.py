"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shopmind import __version__
from shopmind.api.routes import build_router
from shopmind.config import Settings
from shopmind.container import build_container

MAX_BODY_BYTES = 65_536


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_env()
    container = build_container(resolved)
    app = FastAPI(
        title="ShopMind",
        version=__version__,
        summary="Grounded support agent for the fictional store Lume & Co.",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_list,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def guard_body_and_headers(request: Request, call_next):
        length = request.headers.get("content-length")
        if length:
            try:
                if int(length) > MAX_BODY_BYTES:
                    return JSONResponse({"detail": "payload too large"}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "invalid content length"}, status_code=400)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        remaining = getattr(request.state, "rate_remaining", None)
        if remaining is not None:
            response.headers["X-RateLimit-Limit"] = str(resolved.rate_limit_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    @app.get("/")
    def root() -> dict:
        return {
            "service": "shopmind",
            "health": "/api/health",
            "docs": "/api/docs",
            "chat": "/api/chat",
        }

    app.include_router(build_router())
    return app
