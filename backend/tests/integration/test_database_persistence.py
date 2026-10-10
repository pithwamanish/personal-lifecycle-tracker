from __future__ import annotations

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db_models import GroupModel, LifecycleItemModel, UserModel


@pytest.mark.integration
def test_direct_postgresql_persistence_from_api(
    api_client: httpx.Client,
    create_test_user,
    db_session: Session,
):
    """
    Scenario: Cross-tier data persistence.
    Verifies that items created through the live FastAPI HTTP API are committed
    and queryable directly in the PostgreSQL container via SQLAlchemy models and raw SQL.
    """
    user = create_test_user(email_prefix="persist_test")
    item_payload = {
        "name": "Live PostgreSQL Motorcycle Service",
        "lifecycleType": "maintenance",
        "dueDate": "2026-11-15",
    }
    create_res = api_client.post("/api/v1/items", json=item_payload, headers=user["headers"])
    assert create_res.status_code == 201
    item_id = create_res.json()["id"]

    # 1. Query via SQLAlchemy session connected to live PostgreSQL
    db_item = db_session.query(LifecycleItemModel).filter_by(id=item_id).first()
    assert db_item is not None
    assert db_item.name == "Live PostgreSQL Motorcycle Service"
    assert db_item.lifecycle_type == "maintenance"
    assert db_item.due_date == "2026-11-15"
    assert db_item.owner_id == user["id"]

    # 2. Query via raw SQL directly against PostgreSQL
    raw_row = db_session.execute(
        text("SELECT name, lifecycle_type, status FROM items WHERE id = :id"),
        {"id": item_id},
    ).fetchone()
    assert raw_row is not None
    assert raw_row[0] == "Live PostgreSQL Motorcycle Service"
    assert raw_row[1] == "maintenance"
    assert raw_row[2] == "active"


@pytest.mark.integration
def test_group_cascade_deletion_in_postgres(
    api_client: httpx.Client,
    create_test_user,
    db_session: Session,
):
    """
    Scenario: Relational integrity and cascading delete in PostgreSQL.
    Verifies that when a group is deleted via the API, all corresponding records in
    `groups`, `group_members`, and `lifecycle_items` are cascade deleted from PostgreSQL.
    """
    owner = create_test_user(email_prefix="grp_owner")
    member = create_test_user(email_prefix="grp_member")

    # Create group
    grp_res = api_client.post("/api/v1/groups", json={"name": "Cascade Delete Group"}, headers=owner["headers"])
    assert grp_res.status_code == 201
    group_id = grp_res.json()["id"]

    # Add member
    add_res = api_client.post(
        f"/api/v1/groups/{group_id}/members",
        json={"email": member["email"]},
        headers=owner["headers"],
    )
    assert add_res.status_code == 200

    # Create shared item in group
    item_res = api_client.post(
        "/api/v1/items",
        json={
            "name": "Cascade Test Item",
            "lifecycleType": "renewal",
            "dueDate": "2026-12-01",
            "groupId": group_id,
        },
        headers=owner["headers"],
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["id"]

    # Verify item and group exist in PostgreSQL
    assert db_session.query(GroupModel).filter_by(id=group_id).first() is not None
    assert db_session.query(LifecycleItemModel).filter_by(id=item_id).first() is not None

    # Delete group via API
    del_res = api_client.delete(f"/api/v1/groups/{group_id}", headers=owner["headers"])
    assert del_res.status_code == 204

    # Expire and refresh session to verify PostgreSQL state
    db_session.expire_all()
    assert db_session.query(GroupModel).filter_by(id=group_id).first() is None
    assert db_session.query(LifecycleItemModel).filter_by(id=item_id).first() is None

    # Check raw SQL table counts
    members_count = db_session.execute(
        text("SELECT COUNT(*) FROM group_members WHERE group_id = :gid"),
        {"gid": group_id},
    ).scalar()
    assert members_count == 0


@pytest.mark.integration
def test_user_cascade_deletion_in_postgres(
    api_client: httpx.Client,
    create_test_user,
    db_session: Session,
):
    """
    Scenario: User account deletion cascades to owned personal items.
    """
    user = create_test_user(email_prefix="cascade_user")
    user_id = user["id"]

    # Create two items owned by user
    for i in range(2):
        api_client.post(
            "/api/v1/items",
            json={
                "name": f"User Owned Item {i}",
                "lifecycleType": "warranty",
                "dueDate": "2027-01-01",
            },
            headers=user["headers"],
        )

    items_before = db_session.query(LifecycleItemModel).filter_by(owner_id=user_id).count()
    assert items_before == 2

    # Delete user via API
    del_res = api_client.delete(f"/api/v1/users/{user_id}", headers=user["headers"])
    assert del_res.status_code == 204

    db_session.expire_all()
    assert db_session.query(UserModel).filter_by(id=user_id).first() is None
    items_after = db_session.query(LifecycleItemModel).filter_by(owner_id=user_id).count()
    assert items_after == 0


@pytest.mark.integration
def test_group_member_leave_preserves_group_items(
    api_client: httpx.Client,
    create_test_user,
    db_session: Session,
):
    """
    Scenario: Group items persist with the group when a member leaves.
    """
    owner = create_test_user(email_prefix="leave_owner")
    member = create_test_user(email_prefix="leave_member")

    grp_res = api_client.post("/api/v1/groups", json={"name": "Leave Persistence Group"}, headers=owner["headers"])
    group_id = grp_res.json()["id"]

    api_client.post(
        f"/api/v1/groups/{group_id}/members",
        json={"email": member["email"]},
        headers=owner["headers"],
    )

    # Member creates shared item
    item_res = api_client.post(
        "/api/v1/items",
        json={
            "name": "Member Created Shared Appliance Warranty",
            "lifecycleType": "warranty",
            "dueDate": "2028-05-20",
            "groupId": group_id,
        },
        headers=member["headers"],
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["id"]

    # Member leaves group
    leave_res = api_client.post(f"/api/v1/groups/{group_id}/leave", headers=member["headers"])
    assert leave_res.status_code == 200

    # In PostgreSQL: item still exists with groupId
    db_session.expire_all()
    item = db_session.query(LifecycleItemModel).filter_by(id=item_id).first()
    assert item is not None
    assert item.group_id == group_id

    # Owner can still retrieve item via API
    owner_get = api_client.get(f"/api/v1/items/{item_id}", headers=owner["headers"])
    assert owner_get.status_code == 200
    assert owner_get.json()["name"] == "Member Created Shared Appliance Warranty"
