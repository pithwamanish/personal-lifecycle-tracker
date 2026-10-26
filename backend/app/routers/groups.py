from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import get_current_user_optional
from app.models import (
    AddMemberRequest,
    CreateGroupRequest,
    Group,
    MessageResponse,
    User,
)
from app.store import DatabaseStore, get_store
from app.telemetry import record_group_created, record_group_member_invited

router = APIRouter()


@router.get("", response_model=List[Group], status_code=status.HTTP_200_OK)
async def list_groups(
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> List[Group]:
    return store.get_groups(user=current_user)


@router.post("", response_model=Group, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: CreateGroupRequest,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> Group:
    group = store.create_group(user=current_user, name=payload.name)
    record_group_created()
    return group


@router.get("/{id}", response_model=Group, status_code=status.HTTP_200_OK)
async def get_group(
    id: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> Group:
    group = store.get_group_by_id(id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    if not store.is_group_accessible(group, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this group",
        )
    return group


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    id: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> Response:
    group = store.get_group_by_id(id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    deleted, err = store.delete_group(requester=current_user, group_id=id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err or "Could not delete group",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{groupId}/members", response_model=Group, status_code=status.HTTP_200_OK)
async def add_member(
    groupId: str,
    payload: AddMemberRequest,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> Group:
    group = store.get_group_by_id(groupId)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    try:
        updated_group = store.add_member(
            user=current_user, group_id=groupId, email=payload.email
        )
        if not updated_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        record_group_member_invited()
        return updated_group
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{groupId}/members/{memberEmail}", response_model=Group, status_code=status.HTTP_200_OK)
async def remove_member(
    groupId: str,
    memberEmail: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> Group:
    group = store.get_group_by_id(groupId)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    updated_group, err = store.remove_member(
        requester=current_user, group_id=groupId, member_email=memberEmail
    )
    if not updated_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err or "Could not remove member",
        )
    return updated_group


@router.post("/{groupId}/leave", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def leave_group(
    groupId: str,
    current_user: User = Depends(get_current_user_optional),
    store: DatabaseStore = Depends(get_store),
) -> MessageResponse:
    group = store.get_group_by_id(groupId)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    success, err = store.leave_group(user=current_user, group_id=groupId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err or "Could not leave group",
        )
    return MessageResponse(message="Left group successfully")
