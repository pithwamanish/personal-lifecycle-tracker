from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.auth import get_current_user_optional
from app.models import (
    DailyDigestConfig,
    DailyDigestEmail,
    GenerateDigestRequest,
    RemindersSummary,
    UpdateDigestConfigRequest,
    User,
)
from app.store import InMemoryStore, get_store

router = APIRouter()


@router.get("/summary", response_model=RemindersSummary, status_code=status.HTTP_200_OK)
async def get_summary(
    current_user: User = Depends(get_current_user_optional),
    store: InMemoryStore = Depends(get_store),
) -> RemindersSummary:
    return store.get_reminders_summary(user=current_user)


@router.get("/digest/config", response_model=DailyDigestConfig, status_code=status.HTTP_200_OK)
async def get_digest_config(
    store: InMemoryStore = Depends(get_store),
) -> DailyDigestConfig:
    return store.get_digest_config()


@router.patch("/digest/config", response_model=DailyDigestConfig, status_code=status.HTTP_200_OK)
async def update_digest_config(
    payload: UpdateDigestConfigRequest,
    store: InMemoryStore = Depends(get_store),
) -> DailyDigestConfig:
    return store.update_digest_config(data=payload)


@router.post("/digest/generate", response_model=DailyDigestEmail, status_code=status.HTTP_200_OK)
async def generate_digest(
    payload: Optional[GenerateDigestRequest] = None,
    current_user: User = Depends(get_current_user_optional),
    store: InMemoryStore = Depends(get_store),
) -> DailyDigestEmail:
    recipient_email = payload.recipientEmail if payload else None
    return store.generate_digest(user=current_user, recipient_email=recipient_email)


@router.get("/digest/history", response_model=List[DailyDigestEmail], status_code=status.HTTP_200_OK)
async def get_digest_history(
    store: InMemoryStore = Depends(get_store),
) -> List[DailyDigestEmail]:
    return store.get_digest_history()
