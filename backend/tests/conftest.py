from __future__ import annotations

import os
import sys
from typing import Generator

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import get_store


@pytest.fixture(autouse=True)
def reset_store_state():
    """Ensure every test starts with fresh seed data."""
    store = get_store()
    store.seed()
    yield
    store.seed()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_client(client: TestClient) -> TestClient:
    """Alias for backwards compatibility with test_client fixtures."""
    return client


@pytest.fixture
def auth_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    return res.json()["token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}
