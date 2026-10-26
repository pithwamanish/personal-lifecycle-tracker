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
from app.store import DatabaseStore, get_store
from app.telemetry import (
    record_item_completed,
    record_item_created,
    record_item_creation_failure,
    record_item_deleted,
)

router = APIRouter()


@router.get("", response_model=List[LifecycleItem], status_code=status.HTTP_200_OK)
async def list_items(
    groupId: Optional[str] = Query(None, description="Filter by groupId ('null' for personal items)"),
    type: Optional[LifecycleType] = Query(None, description="Filter by lifecycle type"),
    searchQuery: Optional[str] = Query(None, description="Search query string"),
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> List[LifecycleItem]:
    items = store.get_items(
        user=current_user,
        group_id=groupId,
        lifecycle_type=type,
        search_query=searchQuery,
    )
    return items


@router.post("", response_model=LifecycleItem, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: CreateItemDTO,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> LifecycleItem:
    l_type = payload.lifecycleType.value if hasattr(payload.lifecycleType, "value") else str(payload.lifecycleType)
    if not payload.name or not payload.name.strip():
        record_item_creation_failure(l_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item name cannot be empty",
        )
    try:
        item = store.create_item(user=current_user, data=payload)
        record_item_created(item.lifecycleType.value)
        store.sync_metrics()
        return item
    except (ValueError, PermissionError) as exc:
        record_item_creation_failure(l_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        record_item_creation_failure(l_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Item creation failed: {exc}",
        )


@router.get("/{id}", response_model=LifecycleItem, status_code=status.HTTP_200_OK)
async def get_item(
    id: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> LifecycleItem:
    item = store.get_item_by_id(id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    if not store.is_item_accessible(item, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this item",
        )
    return item


@router.patch("/{id}", response_model=LifecycleItem, status_code=status.HTTP_200_OK)
async def update_item(
    id: str,
    payload: UpdateItemDTO,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
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
        store.sync_metrics()
        return updated
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    id: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
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
        record_item_deleted(item.lifecycleType.value)
        store.sync_metrics()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{id}/complete", response_model=LifecycleItem, status_code=status.HTTP_200_OK)
async def toggle_complete(
    id: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> LifecycleItem:
    item = store.get_item_by_id(id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    try:
        updated = store.toggle_item_completion(id, user=current_user)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )
        status_str = updated.status.value if hasattr(updated.status, "value") else str(updated.status)
        if status_str == "completed":
            record_item_completed(updated.lifecycleType.value)
        store.sync_metrics()
        return updated
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
