from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.models import MessageResponse
from app.store import DatabaseStore, get_store

router = APIRouter()


@router.post("/seed", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def reset_seed(
    store: DatabaseStore = Depends(get_store),
) -> MessageResponse:
    store.seed()
    return MessageResponse(message="Seed data loaded successfully")
