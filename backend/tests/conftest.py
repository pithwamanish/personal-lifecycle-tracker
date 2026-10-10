from __future__ import annotations

import os
import sys
from typing import Generator

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Default test database resolution
DEFAULT_TEST_DB_URL = "sqlite:///./test_lifecycle.db"


def get_test_database_url() -> str:
    """
    Returns the database URL for the test session.
    Prioritizes TEST_DATABASE_URL; if not set, defaults to an isolated SQLite file
    so test runs never clobber active development databases.
    """
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_TEST_URL") or DEFAULT_TEST_DB_URL


import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import get_store, reset_store


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Configure store with test database for the entire test session."""
    test_db_url = get_test_database_url()
    reset_store(test_db_url)
    yield
    # Cleanup test db file after session if local file
    if test_db_url.startswith("sqlite:///./") and os.path.exists("./test_lifecycle.db"):
        try:
            os.remove("./test_lifecycle.db")
        except OSError:
            pass


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
