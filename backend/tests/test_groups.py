from __future__ import annotations

from fastapi.testclient import TestClient


def test_groups_lifecycle_and_members(test_client: TestClient):
    # 1. List groups
    list_res = test_client.get("/api/v1/groups")
    assert list_res.status_code == 200
    groups = list_res.json()
    assert len(groups) > 0

    # 2. Create group
    res = test_client.post("/api/v1/groups", json={"name": "Family & Home"})
    assert res.status_code == 201
    group = res.json()
    group_id = group["id"]
    assert group["name"] == "Family & Home"
    assert "alex@example.com" in group["memberEmails"]

    # 3. Get group
    get_res = test_client.get(f"/api/v1/groups/{group_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Family & Home"

    # 4. Add member
    member_res = test_client.post(
        f"/api/v1/groups/{group_id}/members",
        json={"email": "jordan@example.com"},
    )
    assert member_res.status_code == 200
    assert "jordan@example.com" in member_res.json()["memberEmails"]

    # 5. Remove member
    rem_res = test_client.delete(f"/api/v1/groups/{group_id}/members/jordan@example.com")
    assert rem_res.status_code == 200
    assert "jordan@example.com" not in rem_res.json()["memberEmails"]

    # 6. Delete group
    del_res = test_client.delete(f"/api/v1/groups/{group_id}")
    assert del_res.status_code == 204

    # 7. Check not found
    assert test_client.get(f"/api/v1/groups/{group_id}").status_code == 404


def test_owner_cannot_leave_group(test_client: TestClient):
    # user_alex is owner of group_home
    res = test_client.post("/api/v1/groups/group_home/leave")
    assert res.status_code == 400
    assert "error" in res.json()


def test_groups_not_found_errors(test_client: TestClient):
    assert test_client.get("/api/v1/groups/unknown-id").status_code == 404
    assert test_client.delete("/api/v1/groups/unknown-id").status_code == 404
    assert test_client.post("/api/v1/groups/unknown-id/members", json={"email": "a@b.com"}).status_code == 404
    assert test_client.delete("/api/v1/groups/unknown-id/members/a@b.com").status_code == 404
    assert test_client.post("/api/v1/groups/unknown-id/leave").status_code == 404

