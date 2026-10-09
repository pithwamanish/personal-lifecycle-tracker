from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth import get_current_user_optional
from app.models import (
    CreateItemDTO,
    LifecycleItem,
    LifecycleType,
    UpdateItemDTO,
    User,
)
from app.store import InMemoryStore, get_store

router = APIRouter()


@router.get("", response_model=List[LifecycleItem], status_code=status.HTTP_200_OK)
async def list_items(
    groupId: Optional[str] = Query(None, description="Filter by groupId ('null' for personal items)"),
    type: Optional[LifecycleType] = Query(None, description="Filter by lifecycle type"),
    searchQuery: Optional[str] = Query(None, description="Search query string"),
    current_user: User = Depends(get_current_user_optional),
    store: InMemoryStore = Depends(get_store),
) -> List[LifecycleItem]:
    return store.get_items(
        user=current_user,
        group_id=groupId,
        lifecycle_type=type,
        search_query=searchQuery,
    )


@router.post("", response_model=LifecycleItem, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: CreateItemDTO,
    current_user: User = Depends(get_current_user_optional),
    store: InMemoryStore = Depends(get_store),
) -> LifecycleItem:
    try:
        return store.create_item(user=current_user, data=payload)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/{id}", response_model=LifecycleItem, status_code=status.HTTP_200_OK)
async def get_item(
    id: str,
    store: InMemoryStore = Depends(get_store),
) -> LifecycleItem:
    item = store.get_item_by_id(id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


@router.patch("/{id}", response_model=LifecycleItem, status_code=status.HTTP_200_OK)
async def update_item(
    id: str,
    payload: UpdateItemDTO,
    current_user: User = Depends(get_current_user_optional),
    store: InMemoryStore = Depends(get_store),
) -> LifecycleItem:
    item = store.get_item_by_id(id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    try:
        updated = store.update_item(user=current_user, item_id=id, data=payload)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return updated
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    id: str,
    current_user: User = Depends(get_current_user_optional),
    store: InMemoryStore = Depends(get_store),
) -> Response:
    item = store.get_item_by_id(id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    try:
        deleted = store.delete_item(user=current_user, item_id=id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{id}/complete", response_model=LifecycleItem, status_code=status.HTTP_200_OK)
async def toggle_complete(
    id: str,
    store: InMemoryStore = Depends(get_store),
) -> LifecycleItem:
    updated = store.toggle_item_completion(id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return updated
