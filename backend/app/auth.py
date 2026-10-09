from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models import User

SECRET_KEY = os.getenv("JWT_SECRET", "personal-lifecycle-tracker-jwt-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored salt:hash string."""
    try:
        if not hashed_password or ":" not in hashed_password:
            return False
        salt, key_hex = hashed_password.split(":")
        expected_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000
        )
        return secrets.compare_digest(key_hex, expected_key.hex())
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> User:
    """
    Enforces Bearer authentication strictly. Used for /auth/me and protected routes.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.store import get_store
    store = get_store()

    user_id = payload["sub"]
    user_in_db = store.get_user_by_id(user_id)
    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(
        id=user_in_db.id,
        email=user_in_db.email,
        name=user_in_db.name,
        createdAt=user_in_db.createdAt,
    )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> User:
    """
    Resolves the authenticated user if Bearer token is provided.
    If no token is supplied, falls back to the default seed user for dev/demo simplicity.
    If an invalid token is provided, raises 401.
    """
    from app.store import get_store
    store = get_store()

    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_in_db = store.get_user_by_id(payload["sub"])
        if not user_in_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return User(
            id=user_in_db.id,
            email=user_in_db.email,
            name=user_in_db.name,
            createdAt=user_in_db.createdAt,
        )

    default_user = store.get_default_user()
    return User(
        id=default_user.id,
        email=default_user.email,
        name=default_user.name,
        createdAt=default_user.createdAt,
    )
