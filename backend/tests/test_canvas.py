from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.routers.canvas import _reset_canvas_components_store


@pytest.fixture(autouse=True)
def clean_canvas_store():
    _reset_canvas_components_store()
    yield
    _reset_canvas_components_store()


def test_create_and_list_canvas_components(client: TestClient):
    """Test creating and listing canvas components."""
    # List initially empty
    res = client.get("/api/v1/canvas/components")
    assert res.status_code == 200
    assert res.json() == []

    # Create component
    payload = {
        "name": "Navigation Node",
        "componentType": "node",
        "properties": {"x": 100, "y": 200},
    }
    create_res = client.post("/api/v1/canvas/components", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["name"] == "Navigation Node"
    assert data["componentType"] == "node"
    assert data["properties"] == {"x": 100, "y": 200}
    assert "id" in data
    assert "createdAt" in data

    comp_id = data["id"]

    # Get by ID
    get_res = client.get(f"/api/v1/canvas/components/{comp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == comp_id

    # List with filter
    filter_res = client.get("/api/v1/canvas/components?componentType=node")
    assert filter_res.status_code == 200
    assert len(filter_res.json()) == 1

    filter_empty = client.get("/api/v1/canvas/components?componentType=panel")
    assert filter_empty.status_code == 200
    assert len(filter_empty.json()) == 0

    # Delete
    del_res = client.delete(f"/api/v1/canvas/components/{comp_id}")
    assert del_res.status_code == 204

    # 404 after deletion
    get_after_del = client.get(f"/api/v1/canvas/components/{comp_id}")
    assert get_after_del.status_code == 404


def test_canvas_component_creation_validation(client: TestClient):
    """Test validation errors when creating canvas components."""
    # Empty name fails with 400
    res = client.post("/api/v1/canvas/components", json={"name": "", "componentType": "card"})
    assert res.status_code == 400
    assert "error" in res.json()

    # Missing name fails with 400
    res2 = client.post("/api/v1/canvas/components", json={"componentType": "card"})
    assert res2.status_code == 400
