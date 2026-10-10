from __future__ import annotations

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine


@pytest.mark.integration
def test_backend_health_endpoint(api_client: httpx.Client):
    """
    Scenario: Backend service health and database connectivity.
    Validates that the FastAPI backend container is operational and connected to PostgreSQL.
    """
    res = api_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["version"] == "1.0.0"


@pytest.mark.integration
def test_frontend_root_liveness(frontend_client: httpx.Client):
    """
    Scenario: Frontend Vite dev server availability.
    Validates that the React frontend container is running and serving the single-page application.
    """
    res = frontend_client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "<!doctype html>" in res.text.lower() or "<html" in res.text.lower()


@pytest.mark.integration
def test_frontend_reverse_proxy_to_backend(frontend_client: httpx.Client):
    """
    Scenario: Multi-container proxy routing.
    Validates that frontend container's dev proxy forwards requests to the backend container.
    """
    res = frontend_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.integration
def test_cors_preflight_and_headers(api_client: httpx.Client):
    """
    Scenario: Cross-Origin Resource Sharing (CORS) configuration.
    Validates that backend allows origins specified in docker-compose.yaml CORS_ORIGINS.
    """
    origin = "http://localhost:3000"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    res = api_client.options("/api/v1/items", headers=headers)
    assert res.status_code in (200, 204)
    assert res.headers.get("access-control-allow-origin") == origin


@pytest.mark.integration
def test_direct_postgresql_connectivity_and_schema(db_engine: Engine):
    """
    Scenario: Real PostgreSQL database engine, connection pooling, and schema verification.
    Connects directly to the PostgreSQL container and verifies that all application tables exist.
    """
    with db_engine.connect() as conn:
        # Verify engine dialect and version
        result = conn.execute(text("SELECT version()")).scalar()
        assert "PostgreSQL" in result, f"Expected PostgreSQL, got {result}"

        # Verify all core tables exist in PostgreSQL
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = {row[0] for row in conn.execute(query).fetchall()}

        expected_tables = {
            "users",
            "groups",
            "group_members",
            "items",
            "daily_digest_config",
            "daily_digest_history",
        }
        for table in expected_tables:
            assert table in tables, f"Expected table '{table}' in PostgreSQL database schema"
