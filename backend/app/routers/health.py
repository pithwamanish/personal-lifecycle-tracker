from __future__ import annotations

from fastapi import APIRouter
from app.models import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def get_health() -> HealthStatus:
    return HealthStatus(status="healthy", database="connected", version="1.0.0")
