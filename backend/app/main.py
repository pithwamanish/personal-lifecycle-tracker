from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, dev, groups, health, items, reminders, users
from app.telemetry import init_opentelemetry, setup_telemetry_middleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="Personal Lifecycle Tracker API",
        description=(
            "Production REST API for Personal Lifecycle Tracker. "
            "Manages Renewals, Maintenance, and Warranties for independent users and shared groups, "
            "including action summaries and scheduled daily morning email digests."
        ),
        version="1.0.0",
    )

    init_opentelemetry(app)
    setup_telemetry_middleware(app)

    raw_origins = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("AWS_EXECUTION_ENV"))

    # In AWS Lambda, the Lambda Function URL natively attaches CORS headers.
    # Avoid duplicate headers unless specific origins are explicitly configured.
    if not is_lambda or raw_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins if origins else ["*"],
            allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            msg = detail["error"]
        elif isinstance(detail, dict) and "detail" in detail:
            msg = detail["detail"]
        else:
            msg = str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": msg},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        msg = errors[0].get("msg", "Validation error") if errors else "Validation error"
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": msg},
        )

    # Register routers
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(items.router, prefix="/api/v1/items", tags=["items"])
    app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
    app.include_router(reminders.router, prefix="/api/v1/reminders", tags=["reminders"])
    app.include_router(dev.router, prefix="/api/v1/dev", tags=["dev"])

    # Eagerly warm DatabaseStore during container boot
    try:
        from app.store import get_store
        get_store()
    except Exception as e:
        # Avoid crashing container boot if database is temporarily unreachable
        pass

    return app


app = create_app()
