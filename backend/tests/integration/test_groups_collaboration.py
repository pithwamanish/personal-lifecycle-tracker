from __future__ import annotations

import httpx
import pytest


@pytest.mark.integration
def test_group_creation_and_member_invitation(api_client: httpx.Client, create_test_user):
    """
    Scenario: Group creation and member invitation by email.
    """
    owner = create_test_user(email_prefix="grp_lead")
    invitee = create_test_user(email_prefix="grp_join")

    # Create group
    res_grp = api_client.post("/api/v1/groups", json={"name": "Home Maintenance Crew"}, headers=owner["headers"])
    assert res_grp.status_code == 201
    group_id = res_grp.json()["id"]
    assert res_grp.json()["ownerEmail"] == owner["email"]

    # Invite member
    res_invite = api_client.post(
        f"/api/v1/groups/{group_id}/members",
        json={"email": invitee["email"]},
        headers=owner["headers"],
    )
    assert res_invite.status_code == 200
    assert invitee["email"] in res_invite.json()["memberEmails"]


@pytest.mark.integration
def test_cross_user_shared_item_collaboration(api_client: httpx.Client, create_test_user):
    """
    Scenario: Shared group items creation and cross-member editing.
    All group members can create, view, and edit shared items.
    """
    user_a = create_test_user(email_prefix="collab_a")
    user_b = create_test_user(email_prefix="collab_b")

    # User A creates group and invites User B
    grp_res = api_client.post("/api/v1/groups", json={"name": "Shared Fleet"}, headers=user_a["headers"])
    group_id = grp_res.json()["id"]
    api_client.post(f"/api/v1/groups/{group_id}/members", json={"email": user_b["email"]}, headers=user_a["headers"])

    # User B creates shared item
    item_res = api_client.post(
        "/api/v1/items",
        json={
            "name": "Shared Van Oil Change",
            "lifecycleType": "maintenance",
            "dueDate": "2026-11-20",
            "groupId": group_id,
        },
        headers=user_b["headers"],
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["id"]

    # User A lists items for the group and sees User B's item
    list_res = api_client.get(f"/api/v1/items?groupId={group_id}", headers=user_a["headers"])
    assert list_res.status_code == 200
    group_items = list_res.json()
    assert any(it["id"] == item_id for it in group_items)

    # User A updates the item created by User B
    patch_res = api_client.patch(
        f"/api/v1/items/{item_id}",
        json={"name": "Shared Van Full 50k Service"},
        headers=user_a["headers"],
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Shared Van Full 50k Service"

    # User B fetches the item and sees the updated name
    get_res = api_client.get(f"/api/v1/items/{item_id}", headers=user_b["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Shared Van Full 50k Service"


@pytest.mark.integration
def test_unauthorized_non_member_access_denied(api_client: httpx.Client, create_test_user):
    """
    Scenario: Multi-tenant security boundaries.
    Non-member users cannot see group in their group list, cannot access group items,
    and cannot create items in groups they do not belong to.
    """
    owner = create_test_user(email_prefix="sec_owner")
    outsider = create_test_user(email_prefix="sec_outsider")

    # Create group
    grp_res = api_client.post("/api/v1/groups", json={"name": "Private Group"}, headers=owner["headers"])
    group_id = grp_res.json()["id"]

    # Outsider listing groups does not see the private group
    outsider_groups = api_client.get("/api/v1/groups", headers=outsider["headers"]).json()
    assert not any(g["id"] == group_id for g in outsider_groups)

    # Outsider querying group items receives empty list
    outsider_items = api_client.get(f"/api/v1/items?groupId={group_id}", headers=outsider["headers"]).json()
    assert outsider_items == []

    # Outsider tries to create item in group -> rejected with 400
    post_res = api_client.post(
        "/api/v1/items",
        json={"name": "Illegal Item", "lifecycleType": "renewal", "groupId": group_id},
        headers=outsider["headers"],
    )
    assert post_res.status_code == 400
    assert "not authorized" in post_res.json().get("detail", "").lower() or "error" in post_res.json()

    # Outsider cannot invite members to the group
    invite_res = api_client.post(
        f"/api/v1/groups/{group_id}/members",
        json={"email": "hacker@example.com"},
        headers=outsider["headers"],
    )
    assert invite_res.status_code == 400


@pytest.mark.integration
def test_member_removal_and_non_owner_deletion_restriction(api_client: httpx.Client, create_test_user):
    """
    Scenario: Member removal and non-owner deletion rejection.
    """
    owner = create_test_user(email_prefix="perm_owner")
    member = create_test_user(email_prefix="perm_member")

    # Create group and add member
    grp_res = api_client.post("/api/v1/groups", json={"name": "Permission Test Group"}, headers=owner["headers"])
    group_id = grp_res.json()["id"]
    api_client.post(f"/api/v1/groups/{group_id}/members", json={"email": member["email"]}, headers=owner["headers"])

    # Non-owner attempts to delete group -> fails
    del_bad = api_client.delete(f"/api/v1/groups/{group_id}", headers=member["headers"])
    assert del_bad.status_code == 400

    # Owner removes member
    rem_res = api_client.delete(f"/api/v1/groups/{group_id}/members/{member['email']}", headers=owner["headers"])
    assert rem_res.status_code == 200
    assert member["email"] not in rem_res.json()["memberEmails"]

    # Member no longer sees group in list of groups
    member_groups = api_client.get("/api/v1/groups", headers=member["headers"]).json()
    assert not any(g["id"] == group_id for g in member_groups)

    # Member cannot add items to group after removal
    add_item_res = api_client.post(
        "/api/v1/items",
        json={"name": "Item After Removal", "lifecycleType": "renewal", "groupId": group_id},
        headers=member["headers"],
    )
    assert add_item_res.status_code == 400
