from __future__ import annotations

from fastapi.testclient import TestClient


def test_item_creation_with_timezone_aware_due_date(test_client: TestClient):
    """
    Incident Reproduction Test:
    Verifies that items with ISO 8601 strings containing timezone offsets
    (e.g., '2026-11-20T10:00:00+00:00' or '2026-11-20T10:00:00Z')
    do not crash with TypeError: can't compare offset-naive and offset-aware datetimes.
    """
    res = test_client.post(
        "/api/v1/items",
        json={
            "name": "Vehicle Warranty Renewal",
            "lifecycleType": "warranty",
            "dueDate": "2026-11-20T10:00:00+00:00",
        },
    )
    assert res.status_code == 201, f"Expected 201 Created but got {res.status_code}: {res.text}"
    item = res.json()
    assert item["name"] == "Vehicle Warranty Renewal"
    assert item["dueDate"] == "2026-11-20"
    assert item["status"] == "active"
