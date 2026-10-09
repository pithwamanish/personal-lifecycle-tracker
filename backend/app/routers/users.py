from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status

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
    store: DatabaseStore = Depends(get_store),
) -> Response:
    deleted = store.delete_user(userId)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
