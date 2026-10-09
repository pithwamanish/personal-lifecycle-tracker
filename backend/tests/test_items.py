from __future__ import annotations

from fastapi.testclient import TestClient


def test_items_crud_and_completion(test_client: TestClient):
    # 1. List existing seed items
    list_res = test_client.get("/api/v1/items")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) > 0

    # 2. Create item
    res = test_client.post(
        "/api/v1/items",
        json={
            "name": "Passport Renewal",
            "lifecycleType": "renewal",
            "dueDate": "2026-11-20",
        },
    )
    assert res.status_code == 201
    item = res.json()
    item_id = item["id"]
    assert item["name"] == "Passport Renewal"
    assert item["lifecycleType"] == "renewal"
    assert item["status"] == "active"
    assert item["ownerEmail"] == "alex@example.com"

    # 3. Get item by ID
    get_res = test_client.get(f"/api/v1/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == item_id

    # 4. Update item
    patch_res = test_client.patch(
        f"/api/v1/items/{item_id}",
        json={"name": "Updated Passport Renewal", "dueDate": "2026-12-01"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated Passport Renewal"
    assert patch_res.json()["dueDate"] == "2026-12-01"

    # 5. Toggle complete
    complete_res = test_client.post(f"/api/v1/items/{item_id}/complete")
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

    # Toggle back to active
    active_res = test_client.post(f"/api/v1/items/{item_id}/complete")
    assert active_res.status_code == 200
    assert active_res.json()["status"] == "active"

    # 6. Delete item
    del_res = test_client.delete(f"/api/v1/items/{item_id}")
    assert del_res.status_code == 204

    # 7. Verify deletion
    not_found_res = test_client.get(f"/api/v1/items/{item_id}")
    assert not_found_res.status_code == 404


def test_items_filtering(test_client: TestClient):
    # Filter by type
    renewals_res = test_client.get("/api/v1/items?type=renewal")
    assert renewals_res.status_code == 200
    for itm in renewals_res.json():
        assert itm["lifecycleType"] == "renewal"

    # Filter personal only (groupId=null)
    personal_res = test_client.get("/api/v1/items?groupId=null")
    assert personal_res.status_code == 200
    for itm in personal_res.json():
        assert itm["groupId"] is None

    # Filter specific group
    group_res = test_client.get("/api/v1/items?groupId=group_home")
    assert group_res.status_code == 200
    for itm in group_res.json():
        assert itm["groupId"] == "group_home"

    # Search query
    search_res = test_client.get("/api/v1/items?searchQuery=Auto")
    assert search_res.status_code == 200
    assert any("Auto" in itm["name"] for itm in search_res.json())


def test_create_item_with_auth_bearer(test_client: TestClient):
    # Signup a distinct user
    signup_res = test_client.post(
        "/api/v1/auth/signup",
        json={"email": "beareruser@example.com", "name": "Bearer User", "password": "password123"},
    )
    token = signup_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create item with Bearer header
    res = test_client.post(
        "/api/v1/items",
        json={"name": "Bicycle Service", "lifecycleType": "maintenance"},
        headers=headers,
    )
    assert res.status_code == 201
    item = res.json()
    assert item["ownerEmail"] == "beareruser@example.com"
    assert item["name"] == "Bicycle Service"


def test_items_not_found_errors(test_client: TestClient):
    assert test_client.get("/api/v1/items/non-existent-id").status_code == 404
    assert test_client.patch("/api/v1/items/non-existent-id", json={"name": "X"}).status_code == 404
    assert test_client.delete("/api/v1/items/non-existent-id").status_code == 404
    assert test_client.post("/api/v1/items/non-existent-id/complete").status_code == 404

