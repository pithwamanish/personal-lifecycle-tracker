from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.models import MessageResponse
from app.store import DatabaseStore, get_store

router = APIRouter()


@router.post("/seed", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def reset_seed(
    store: DatabaseStore = Depends(get_store),
) -> MessageResponse:
    if os.getenv("APP_ENV") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seed endpoint is disabled in production",
        )
    store.seed()
    return MessageResponse(message="Seed data loaded successfully")
