from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_users(test_client: TestClient):
    res = test_client.get("/api/v1/users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3
    emails = [u["email"] for u in users]
    assert "alex@example.com" in emails
    assert "sarah@example.com" in emails
    assert "jordan@example.com" in emails


def test_delete_user_not_found(test_client: TestClient):
    res = test_client.delete("/api/v1/users/non-existent-user-id")
    assert res.status_code == 404
    assert "error" in res.json()


def test_delete_user_cascade(test_client: TestClient):
    # Deleting user_alex cascades to alex's owned items and groups
    res = test_client.delete("/api/v1/users/user_alex")
    assert res.status_code == 204

    # Verify user is gone
    users_res = test_client.get("/api/v1/users")
    emails = [u["email"] for u in users_res.json()]
    assert "alex@example.com" not in emails

    # Verify group_home (owned by alex) is removed
    groups_res = test_client.get("/api/v1/groups")
    group_ids = [g["id"] for g in groups_res.json()]
    assert "group_home" not in group_ids
