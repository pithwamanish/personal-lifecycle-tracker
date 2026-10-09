from __future__ import annotations

from fastapi.testclient import TestClient


def test_dev_seed_reset(test_client: TestClient):
    # Mutate data by deleting an item
    items_before = test_client.get("/api/v1/items").json()
    assert len(items_before) > 0
    first_id = items_before[0]["id"]
    test_client.delete(f"/api/v1/items/{first_id}")

    # Re-seed
    seed_res = test_client.post("/api/v1/dev/seed")
    assert seed_res.status_code == 200
    assert seed_res.json()["message"] == "Seed data loaded successfully"

    # Verify data is restored
    items_after = test_client.get("/api/v1/items").json()
    assert len(items_after) == 12
