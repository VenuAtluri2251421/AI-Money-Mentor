"""
backend/main.py — FastAPI application factory.

Kept intentionally thin — all business logic lives in routes/services/engine.
The lifespan function handles DB init/teardown so the app is ready before it
accepts its first request and cleans up properly on SIGTERM (important for Docker).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.db import close_db, init_db
from backend.routes.calculate import router as calc_router
from backend.routes.advisor import router as advisor_router
from backend.routes.upload import router as upload_router
from backend.routes.auth import router as auth_router
from backend.routes.profile import router as profile_router
from backend.routes.portfolio import router as portfolio_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    await init_db()
    yield
    logger.info("Shutting down %s", settings.app_name)
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "AI-powered personal finance platform — "
            "SIP, FIRE, Tax, XIRR, Health Score & Artha AI Advisor (ET AI Hackathon 2026)"
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(calc_router, prefix="/api/v1")
    app.include_router(advisor_router, prefix="/api/v1")
    app.include_router(upload_router, prefix="/api/v1")
    app.include_router(profile_router, prefix="/api/v1")
    app.include_router(portfolio_router, prefix="/api/v1")

    @app.get("/health", tags=["System"])
    async def health_check():
        return JSONResponse({"status": "ok", "app": settings.app_name, "env": settings.app_env})

    @app.get("/", tags=["System"])
    async def root():
        return {"message": f"Welcome to {settings.app_name}. Visit /docs for the API reference."}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
