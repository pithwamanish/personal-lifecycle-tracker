from __future__ import annotations

from fastapi import APIRouter, Depends
from app.models import HealthStatus
from app.store import DatabaseStore, get_store

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def get_health(store: DatabaseStore = Depends(get_store)) -> HealthStatus:
    is_connected = store.check_health()
    return HealthStatus(
        status="healthy" if is_connected else "unhealthy",
        database="connected" if is_connected else "disconnected",
        version="1.0.0",
    )
