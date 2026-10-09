from __future__ import annotations

from fastapi.testclient import TestClient


def test_reminders_summary_and_digest(test_client: TestClient):
    # 1. Reminders summary
    summary_res = test_client.get("/api/v1/reminders/summary")
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert "overdue" in data
    assert "upcoming" in data
    assert "totalActiveReminders" in data
    assert data["totalActiveReminders"] == len(data["overdue"]) + len(data["upcoming"])

    # 2. Get and update digest config
    config_res = test_client.get("/api/v1/reminders/digest/config")
    assert config_res.status_code == 200
    config_data = config_res.json()
    assert config_data["deliveryTime"] == "08:00"

    patch_res = test_client.patch(
        "/api/v1/reminders/digest/config",
        json={"deliveryTime": "09:00", "timeZone": "America/New_York"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["deliveryTime"] == "09:00"
    assert patch_res.json()["timeZone"] == "America/New_York"

    # 3. Generate daily digest
    digest_res = test_client.post(
        "/api/v1/reminders/digest/generate",
        json={"recipientEmail": "alex@example.com"},
    )
    assert digest_res.status_code == 200
    digest_data = digest_res.json()
    assert digest_data["deliveryTime"] == "09:00"
    assert digest_data["recipientEmail"] == "alex@example.com"
    assert "htmlContent" in digest_data
    assert "textContent" in digest_data
    assert "overdueItems" in digest_data
    assert "upcomingItems" in digest_data

    # 4. Check digest history
    history_res = test_client.get("/api/v1/reminders/digest/history")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    assert history[0]["id"] == digest_data["id"]


def test_digest_all_clear_generation(test_client: TestClient):
    # Jordan has no personal items and group_vehicles has 2 items (1 overdue, 1 upcoming)
    # Register an isolated brand new user with 0 items
    signup_res = test_client.post(
        "/api/v1/auth/signup",
        json={"email": "fresh@example.com", "name": "Fresh User", "password": "password123"},
    )
    token = signup_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    digest_res = test_client.post(
        "/api/v1/reminders/digest/generate",
        json={"recipientEmail": "fresh@example.com"},
        headers=headers,
    )
    assert digest_res.status_code == 200
    digest = digest_res.json()
    assert digest["overdueCount"] == 0
    assert digest["upcomingCount"] == 0
    assert "All clear for today" in digest["subject"]

