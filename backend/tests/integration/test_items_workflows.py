from __future__ import annotations

import httpx
import pytest


@pytest.mark.integration
def test_create_all_three_lifecycle_types(api_client: httpx.Client, create_test_user):
    """
    Scenario: Support for all 3 MVP lifecycle types (Renewals, Maintenance, Warranties).
    Creates one of each type and verifies response schemas.
    """
    user = create_test_user(email_prefix="items_crud")

    # 1. Renewal with due date
    res_renewal = api_client.post(
        "/api/v1/items",
        json={"name": "Passport Renewal", "lifecycleType": "renewal", "dueDate": "2026-11-01"},
        headers=user["headers"],
    )
    assert res_renewal.status_code == 201
    assert res_renewal.json()["lifecycleType"] == "renewal"
    assert res_renewal.json()["dueDate"] == "2026-11-01"

    # 2. Maintenance with optional (missing) due date
    res_maint = api_client.post(
        "/api/v1/items",
        json={"name": "HVAC Filter Inspection", "lifecycleType": "maintenance"},
        headers=user["headers"],
    )
    assert res_maint.status_code == 201
    assert res_maint.json()["lifecycleType"] == "maintenance"
    assert res_maint.json()["dueDate"] is None

    # 3. Warranty with future due date
    res_warr = api_client.post(
        "/api/v1/items",
        json={"name": "OLED TV 3-Year Protection", "lifecycleType": "warranty", "dueDate": "2028-12-31"},
        headers=user["headers"],
    )
    assert res_warr.status_code == 201
    assert res_warr.json()["lifecycleType"] == "warranty"


@pytest.mark.integration
def test_list_items_and_filtering(api_client: httpx.Client, create_test_user):
    """
    Scenario: Listing, type filtering, and query search on items.
    """
    user = create_test_user(email_prefix="items_filter")

    # Seed 3 items
    api_client.post(
        "/api/v1/items",
        json={"name": "Auto Insurance Renewal", "lifecycleType": "renewal", "dueDate": "2026-10-30"},
        headers=user["headers"],
    )
    api_client.post(
        "/api/v1/items",
        json={"name": "Car Oil Change", "lifecycleType": "maintenance", "dueDate": "2026-11-10"},
        headers=user["headers"],
    )
    api_client.post(
        "/api/v1/items",
        json={"name": "Blender Warranty", "lifecycleType": "warranty", "dueDate": "2027-01-15"},
        headers=user["headers"],
    )

    # List all items for user
    res_all = api_client.get("/api/v1/items", headers=user["headers"])
    assert res_all.status_code == 200
    items = res_all.json()
    assert len(items) >= 3

    # Filter by type=renewal
    res_ren = api_client.get("/api/v1/items?type=renewal", headers=user["headers"])
    assert res_ren.status_code == 200
    renewal_items = res_ren.json()
    assert all(it["lifecycleType"] == "renewal" for it in renewal_items)
    assert any(it["name"] == "Auto Insurance Renewal" for it in renewal_items)

    # Search query
    res_search = api_client.get("/api/v1/items?searchQuery=Blender", headers=user["headers"])
    assert res_search.status_code == 200
    search_items = res_search.json()
    assert len(search_items) == 1
    assert search_items[0]["name"] == "Blender Warranty"


@pytest.mark.integration
def test_get_and_patch_item(api_client: httpx.Client, create_test_user):
    """
    Scenario: Item retrieval by ID and updating fields.
    """
    user = create_test_user(email_prefix="items_patch")
    create_res = api_client.post(
        "/api/v1/items",
        json={"name": "Initial Item Name", "lifecycleType": "renewal", "dueDate": "2026-10-20"},
        headers=user["headers"],
    )
    item_id = create_res.json()["id"]

    # Retrieve by ID
    get_res = api_client.get(f"/api/v1/items/{item_id}", headers=user["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["id"] == item_id

    # Update name and due date
    patch_res = api_client.patch(
        f"/api/v1/items/{item_id}",
        json={"name": "Updated Item Name", "dueDate": "2026-12-25"},
        headers=user["headers"],
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated Item Name"
    assert patch_res.json()["dueDate"] == "2026-12-25"


@pytest.mark.integration
def test_toggle_item_completion(api_client: httpx.Client, create_test_user):
    """
    Scenario: Completion toggle and retention in main list.
    Completed items remain retained in list and can be toggled back.
    """
    user = create_test_user(email_prefix="items_complete")
    create_res = api_client.post(
        "/api/v1/items",
        json={"name": "Dryer Vent Cleaning", "lifecycleType": "maintenance", "dueDate": "2026-10-15"},
        headers=user["headers"],
    )
    item_id = create_res.json()["id"]
    assert create_res.json()["status"] == "active"

    # Toggle to complete
    comp_res = api_client.post(f"/api/v1/items/{item_id}/complete", headers=user["headers"])
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"

    # Verify item is retained in list
    list_res = api_client.get("/api/v1/items", headers=user["headers"])
    assert list_res.status_code == 200
    completed_item = next(it for it in list_res.json() if it["id"] == item_id)
    assert completed_item["status"] == "completed"

    # Toggle back to active
    toggle_back = api_client.post(f"/api/v1/items/{item_id}/complete", headers=user["headers"])
    assert toggle_back.status_code == 200
    assert toggle_back.json()["status"] == "active"


@pytest.mark.integration
def test_delete_item_permanently(api_client: httpx.Client, create_test_user):
    """
    Scenario: Permanent item deletion.
    """
    user = create_test_user(email_prefix="items_del")
    create_res = api_client.post(
        "/api/v1/items",
        json={"name": "Item To Delete", "lifecycleType": "warranty"},
        headers=user["headers"],
    )
    item_id = create_res.json()["id"]

    # Delete
    del_res = api_client.delete(f"/api/v1/items/{item_id}", headers=user["headers"])
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    get_res = api_client.get(f"/api/v1/items/{item_id}", headers=user["headers"])
    assert get_res.status_code == 404


@pytest.mark.integration
def test_item_validation_errors(api_client: httpx.Client, create_test_user):
    """
    Scenario: Input validation and bad request handling.
    """
    user = create_test_user(email_prefix="items_invalid")

    # Invalid lifecycleType
    bad_type = api_client.post(
        "/api/v1/items",
        json={"name": "Bad Item", "lifecycleType": "invalid_type"},
        headers=user["headers"],
    )
    assert bad_type.status_code in (400, 422)

    # Missing required name
    bad_name = api_client.post(
        "/api/v1/items",
        json={"lifecycleType": "renewal"},
        headers=user["headers"],
    )
    assert bad_name.status_code in (400, 422)
