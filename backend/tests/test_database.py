from __future__ import annotations

import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine.url import make_url

from app.database import create_engine_for_url, get_database_url
from app.models import CreateItemDTO, LifecycleType
from app.store import DatabaseStore, get_store


def test_database_url_resolution(monkeypatch):
    # Default fallback
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_URL", raising=False)
    assert get_database_url() == "sqlite:///./lifecycle.db"

    # DB_URL fallback
    monkeypatch.setenv("DB_URL", "sqlite:///./custom.db")
    assert get_database_url() == "sqlite:///./custom.db"

    # DATABASE_URL priority
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./priority.db")
    assert get_database_url() == "sqlite:///./priority.db"

    # Postgres URL scheme normalization (e.g. for future PostgreSQL support)
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost:5432/lifecycledb")
    normalized = get_database_url()
    assert normalized == "postgresql://user:pass@localhost:5432/lifecycledb"
    parsed = make_url(normalized)
    assert parsed.drivername == "postgresql"
    assert parsed.host == "localhost"
    assert parsed.port == 5432
    assert parsed.database == "lifecycledb"


def test_database_engine_dialect_handling():
    # SQLite engine creation
    sqlite_engine = create_engine_for_url("sqlite:///:memory:")
    assert sqlite_engine.dialect.name == "sqlite"


def test_sqlite_persistence_across_connections():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_file = os.path.join(temp_dir, "test_persist.db")
        db_url = f"sqlite:///{db_file}"

        # 1. Initialize store instance 1 and seed
        store_1 = DatabaseStore(database_url=db_url)
        store_1.seed()

        user = store_1.get_default_user()
        new_item = store_1.create_item(
            user=user,
            data=CreateItemDTO(
                name="Persistent Refrigerator Warranty",
                lifecycleType=LifecycleType.warranty,
                dueDate="2027-01-01",
            ),
        )
        assert new_item.name == "Persistent Refrigerator Warranty"
        item_id = new_item.id

        # 2. Initialize brand new store instance 2 pointing to the exact same file
        store_2 = DatabaseStore(database_url=db_url)
        # Should not wipe existing data because user count > 0
        persisted_item = store_2.get_item_by_id(item_id)
        assert persisted_item is not None
        assert persisted_item.name == "Persistent Refrigerator Warranty"
        assert persisted_item.lifecycleType == LifecycleType.warranty


def test_database_healthcheck_endpoint(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
