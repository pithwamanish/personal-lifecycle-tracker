from __future__ import annotations

import os
import uuid
from typing import Generator, Dict, Any

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session


def resolve_service_url(env_var: str, primary_url: str, fallback_url: str, probe_path: str = "/health") -> str:
    """
    Resolves the live service URL, checking the primary container network URL first
    and falling back to the localhost port if primary is unreachable.
    """
    custom = os.environ.get(env_var)
    if custom:
        return custom

    # Try primary URL (e.g. http://backend:8000)
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get(f"{primary_url}{probe_path}")
            if resp.status_code < 500:
                return primary_url
    except Exception:
        pass

    # Try fallback URL (e.g. http://localhost:8003)
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get(f"{fallback_url}{probe_path}")
            if resp.status_code < 500:
                return fallback_url
    except Exception:
        pass

    return primary_url


def resolve_db_url() -> str:
    """Resolves PostgreSQL database URL for container or host network."""
    custom = os.environ.get("INTEGRATION_DB_URL") or os.environ.get("DATABASE_URL")
    if custom and ("postgres" in custom):
        return custom

    # Primary container network URL
    primary = "postgresql://postgres:postgres@db:5432/lifecycle"
    try:
        eng = create_engine(primary, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        return primary
    except Exception:
        pass

    # Fallback host network URL
    fallback = "postgresql://postgres:postgres@localhost:5434/lifecycle"
    return fallback


@pytest.fixture(scope="session")
def live_backend_url() -> str:
    return resolve_service_url("INTEGRATION_BACKEND_URL", "http://backend:8000", "http://localhost:8003", "/health")


@pytest.fixture(scope="session")
def live_frontend_url() -> str:
    return resolve_service_url("INTEGRATION_FRONTEND_URL", "http://frontend:3000", "http://localhost:3003", "/")


@pytest.fixture(scope="session")
def live_db_url() -> str:
    return resolve_db_url()


@pytest.fixture(scope="session", autouse=True)
def verify_services_healthy(live_backend_url: str):
    """
    Ensures backend service is alive before running any integration tests.
    Skips the integration suite cleanly if docker-compose services are not running.
    """
    try:
        with httpx.Client(timeout=3.0) as client:
            res = client.get(f"{live_backend_url}/health")
            if res.status_code != 200:
                pytest.skip(f"Backend at {live_backend_url} returned status {res.status_code}, skipping integration suite.")
    except Exception as exc:
        pytest.skip(
            f"Cannot connect to backend service at {live_backend_url} ({exc}). "
            "Integration tests require running docker-compose containers (run 'make up' or 'docker compose up -d')."
        )


@pytest.fixture(autouse=True)
def reset_store_state():
    """
    Override parent conftest autouse fixture so in-process SQLite store
    is not needlessly reseeded on each live container integration test.
    """
    yield


@pytest.fixture(scope="session")
def db_engine(live_db_url: str) -> Generator[Engine, None, None]:
    engine = create_engine(live_db_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def api_client(live_backend_url: str) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=live_backend_url, timeout=15.0) as client:
        yield client


@pytest.fixture
def frontend_client(live_frontend_url: str) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=live_frontend_url, timeout=15.0) as client:
        yield client


@pytest.fixture(scope="session")
def reset_live_db(live_backend_url: str):
    """Resets the live database to initial seed state."""
    with httpx.Client(base_url=live_backend_url, timeout=10.0) as client:
        res = client.post("/api/v1/dev/seed")
        assert res.status_code == 200, f"Failed to seed live database: {res.text}"


@pytest.fixture
def alex_auth_headers(api_client: httpx.Client) -> Dict[str, str]:
    res = api_client.post("/api/v1/auth/login", json={"email": "alex@example.com", "password": "password123"})
    assert res.status_code == 200, f"Alex login failed: {res.text}"
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sarah_auth_headers(api_client: httpx.Client) -> Dict[str, str]:
    res = api_client.post("/api/v1/auth/login", json={"email": "sarah@example.com", "password": "password123"})
    assert res.status_code == 200, f"Sarah login failed: {res.text}"
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def jordan_auth_headers(api_client: httpx.Client) -> Dict[str, str]:
    res = api_client.post("/api/v1/auth/login", json={"email": "jordan@example.com", "password": "password123"})
    assert res.status_code == 200, f"Jordan login failed: {res.text}"
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def create_test_user(api_client: httpx.Client):
    """Factory creating an isolated user for test isolation."""
    created_user_ids = []

    def _factory(email_prefix: str = "itest", name: str = "Integration Test User") -> Dict[str, Any]:
        random_suffix = uuid.uuid4().hex[:8]
        email = f"{email_prefix}_{random_suffix}@example.com"
        password = "Password123!"

        res = api_client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": password, "name": f"{name} {random_suffix}"},
        )
        assert res.status_code == 201, f"Failed to create test user: {res.text}"
        data = res.json()
        user_id = data["user"]["id"]
        created_user_ids.append(user_id)
        token = data["token"]

        return {
            "id": user_id,
            "email": email,
            "password": password,
            "name": data["user"]["name"],
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    yield _factory

    # Teardown: delete created test users
    for uid in created_user_ids:
        try:
            # Login as Alex (or cleanup directly)
            alex_res = api_client.post("/api/v1/auth/login", json={"email": "alex@example.com", "password": "password123"})
            if alex_res.status_code == 200:
                alex_headers = {"Authorization": f"Bearer {alex_res.json()['token']}"}
                api_client.delete(f"/api/v1/users/{uid}", headers=alex_headers)
        except Exception:
            pass
