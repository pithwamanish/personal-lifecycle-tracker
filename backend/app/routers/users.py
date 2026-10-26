from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import get_current_user_optional
from app.models import User
from app.store import DatabaseStore, get_store

router = APIRouter()


@router.get("", response_model=List[User], status_code=status.HTTP_200_OK)
async def list_users(
    store: DatabaseStore = Depends(get_store),
) -> List[User]:
    return store.list_users()


@router.delete("/{userId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    userId: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> Response:
    target_user = store.get_user_by_id(userId)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if current_user.id != userId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this account",
        )
    deleted = store.delete_user(userId)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
