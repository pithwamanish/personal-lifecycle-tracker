from __future__ import annotations

import httpx
import pytest


@pytest.mark.integration
def test_reminders_summary_aggregates_overdue_and_upcoming(
    api_client: httpx.Client,
    create_test_user,
):
    """
    Scenario: Reminders summary calculations.
    Validates that /api/v1/reminders/summary calculates overdue and upcoming items.
    """
    user = create_test_user(email_prefix="rem_summary")

    # Create an overdue item
    api_client.post(
        "/api/v1/items",
        json={"name": "Overdue Passport", "lifecycleType": "renewal", "dueDate": "2020-01-01"},
        headers=user["headers"],
    )

    # Create an upcoming item (due in 5 days, or within upcoming window)
    api_client.post(
        "/api/v1/items",
        json={"name": "Upcoming Car Checkup", "lifecycleType": "maintenance", "dueDate": "2026-10-14"},
        headers=user["headers"],
    )

    res = api_client.get("/api/v1/reminders/summary", headers=user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "overdue" in data
    assert "upcoming" in data
    assert "totalActiveReminders" in data
    assert data["totalActiveReminders"] >= 1
    assert any(it["name"] == "Overdue Passport" for it in data["overdue"])


@pytest.mark.integration
def test_daily_digest_config_crud(api_client: httpx.Client, alex_auth_headers):
    """
    Scenario: Daily digest configuration retrieval and updating.
    """
    # 1. Fetch current config
    get_res = api_client.get("/api/v1/reminders/digest/config", headers=alex_auth_headers)
    assert get_res.status_code == 200
    config = get_res.json()
    assert "timeZone" in config
    assert "deliveryTime" in config
    assert config["enabled"] is True

    # 2. Update config
    patch_res = api_client.patch(
        "/api/v1/reminders/digest/config",
        json={"deliveryTime": "09:00", "timeZone": "America/New_York"},
        headers=alex_auth_headers,
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["deliveryTime"] == "09:00"
    assert updated["timeZone"] == "America/New_York"


@pytest.mark.integration
def test_generate_daily_digest_email_and_history(api_client: httpx.Client, alex_auth_headers):
    """
    Scenario: Daily digest generation and history logging.
    """
    # Generate digest email
    gen_res = api_client.post("/api/v1/reminders/digest/generate", headers=alex_auth_headers)
    assert gen_res.status_code == 200
    digest = gen_res.json()
    assert "subject" in digest
    assert "htmlContent" in digest
    assert "textContent" in digest
    assert "overdueCount" in digest
    assert "upcomingCount" in digest
    assert digest["recipientEmail"] == "alex@example.com"
    digest_id = digest["id"]

    # Verify digest appears in history
    hist_res = api_client.get("/api/v1/reminders/digest/history", headers=alex_auth_headers)
    assert hist_res.status_code == 200
    history_list = hist_res.json()
    assert any(item["id"] == digest_id for item in history_list)
