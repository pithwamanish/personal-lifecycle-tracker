from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    User,
)
from app.store import InMemoryStore, get_store

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    store: InMemoryStore = Depends(get_store),
) -> AuthResponse:
    existing = store.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    hashed_pw = hash_password(payload.password)
    user_db = store.create_user(
        email=payload.email,
        name=payload.name,
        hashed_password=hashed_pw,
    )
    user = User(
        id=user_db.id,
        email=user_db.email,
        name=user_db.name,
        createdAt=user_db.createdAt,
    )
    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(user=user, token=token)


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    store: InMemoryStore = Depends(get_store),
) -> AuthResponse:
    user_db = store.get_user_by_email(payload.email)
    if not user_db or not verify_password(payload.password, user_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = User(
        id=user_db.id,
        email=user_db.email,
        name=user_db.name,
        createdAt=user_db.createdAt,
    )
    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(user=user, token=token)


@router.get("/me", response_model=User, status_code=status.HTTP_200_OK)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout() -> MessageResponse:
    return MessageResponse(message="Logged out successfully")
