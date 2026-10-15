from __future__ import annotations

import json
import os
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Generator, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import hash_password
from app.database import (
    check_db_health,
    create_engine_for_url,
    get_database_url,
    init_db,
    is_postgres_url,
    wait_for_db,
)
from app.db_models import (
    DailyDigestConfigModel,
    DailyDigestHistoryModel,
    GroupMemberModel,
    GroupModel,
    LifecycleItemModel,
    UserModel,
)
from app.models import (
    CreateItemDTO,
    DailyDigestConfig,
    DailyDigestEmail,
    DigestDeliveryTime,
    Group,
    ItemStatus,
    ItemUrgency,
    LifecycleItem,
    LifecycleType,
    RemindersSummary,
    UpdateDigestConfigRequest,
    UpdateItemDTO,
    User,
    UserInDB,
)


def get_current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_today_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_relative_date_str(days_offset: int) -> str:
    target = datetime.now(timezone.utc) + timedelta(days=days_offset)
    return target.strftime("%Y-%m-%d")


def get_days_difference(due_date_str: Optional[str], today_str: Optional[str] = None) -> Optional[int]:
    if not due_date_str:
        return None
    today = today_str or get_today_date_str()
    try:
        due = datetime.strptime(due_date_str[:10], "%Y-%m-%d").date()
        curr = datetime.strptime(today[:10], "%Y-%m-%d").date()
        return (due - curr).days
    except ValueError:
        return None


def get_item_urgency(
    item: LifecycleItem, today_str: Optional[str] = None, upcoming_window_days: int = 30
) -> ItemUrgency:
    if item.status == ItemStatus.completed:
        return ItemUrgency.completed
    if not item.dueDate:
        return ItemUrgency.no_date

    clean_today = today_str or get_today_date_str()
    clean_due = item.dueDate[:10]

    if clean_due < clean_today:
        return ItemUrgency.overdue

    diff = get_days_difference(clean_due, clean_today)
    if diff is not None and 0 <= diff <= upcoming_window_days:
        return ItemUrgency.upcoming

    return ItemUrgency.normal


def format_display_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "No due date"
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def get_relative_due_date_label(
    due_date_str: Optional[str], status: ItemStatus, today_str: Optional[str] = None
) -> str:
    if status == ItemStatus.completed:
        return "Completed"
    if not due_date_str:
        return "No due date"

    diff = get_days_difference(due_date_str, today_str)
    if diff is None:
        return "No due date"
    if diff < 0:
        abs_diff = abs(diff)
        return "1 day overdue" if abs_diff == 1 else f"{abs_diff} days overdue"
    if diff == 0:
        return "Due today"
    if diff == 1:
        return "Due tomorrow"
    return f"Due in {diff} days"


class DatabaseStore:
    """
    Database-agnostic persistent store powered by SQLAlchemy.
    Configured via environment variable (DATABASE_URL / DB_URL), supporting
    SQLite by default as well as PostgreSQL and other SQL backends.
    """

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or get_database_url()
        self.engine: Engine = create_engine_for_url(self.database_url)
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine,
        )
        self._lock = threading.Lock()
        # Avoid expensive WAN schema inspection and table count on every serverless cold start
        is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("AWS_EXECUTION_ENV"))
        skip_init = (is_lambda or os.getenv("SKIP_DB_INIT") == "1") and os.getenv("FORCE_INIT_DB") != "1"

        if not skip_init:
            # For remote databases like PostgreSQL, wait briefly for connection readiness
            if is_postgres_url(self.database_url):
                wait_for_db(self.engine, max_retries=15, delay=0.5)

            # Initialize schema tables
            init_db(self.engine)

            # Auto-seed if database is empty on initialization
            with self.get_session() as session:
                user_count = session.query(UserModel).count()
                if user_count == 0:
                    self.seed()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session: Session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def check_health(self) -> bool:
        return check_db_health(self.engine)

    def seed(self) -> None:
        """Seed the database with default users, groups, and items."""
        with self._lock, self.get_session() as session:
            # Clear all existing tables in reverse dependency order
            session.query(DailyDigestHistoryModel).delete(synchronize_session=False)
            session.query(DailyDigestConfigModel).delete(synchronize_session=False)
            session.query(LifecycleItemModel).delete(synchronize_session=False)
            session.query(GroupMemberModel).delete(synchronize_session=False)
            session.query(GroupModel).delete(synchronize_session=False)
            session.query(UserModel).delete(synchronize_session=False)

            # 1. Seed Digest Config
            digest_cfg = DailyDigestConfigModel(
                id=1,
                time_zone="UTC",
                delivery_time=DigestDeliveryTime.TIME_08.value,
                enabled=True,
            )
            session.add(digest_cfg)

            # 2. Seed Users
            default_password_hash = hash_password("password123")
            users_data = [
                UserModel(
                    id="user_alex",
                    email="alex@example.com",
                    name="Alex Taylor",
                    created_at="2026-01-10T08:00:00Z",
                    hashed_password=default_password_hash,
                ),
                UserModel(
                    id="user_sarah",
                    email="sarah@example.com",
                    name="Sarah Jenkins",
                    created_at="2026-02-14T09:30:00Z",
                    hashed_password=default_password_hash,
                ),
                UserModel(
                    id="user_jordan",
                    email="jordan@example.com",
                    name="Jordan Patel",
                    created_at="2026-03-01T11:15:00Z",
                    hashed_password=default_password_hash,
                ),
            ]
            session.add_all(users_data)
            session.flush()

            # 3. Seed Groups & Group Members
            group_home = GroupModel(
                id="group_home",
                name="Oakridge Family & Home",
                owner_id="user_alex",
                owner_email="alex@example.com",
                created_at="2026-02-15T10:00:00Z",
            )
            group_vehicles = GroupModel(
                id="group_vehicles",
                name="Shared Vehicle Maintenance",
                owner_id="user_sarah",
                owner_email="sarah@example.com",
                created_at="2026-02-20T14:00:00Z",
            )
            session.add_all([group_home, group_vehicles])
            session.flush()

            members_data = [
                GroupMemberModel(group_id="group_home", email="alex@example.com"),
                GroupMemberModel(group_id="group_home", email="sarah@example.com"),
                GroupMemberModel(group_id="group_vehicles", email="sarah@example.com"),
                GroupMemberModel(group_id="group_vehicles", email="alex@example.com"),
                GroupMemberModel(group_id="group_vehicles", email="jordan@example.com"),
            ]
            session.add_all(members_data)
            session.flush()

            # 4. Seed Items (12 items matching the frontend seed dataset)
            seed_items = [
                # Renewals
                LifecycleItemModel(
                    id="item_1",
                    name="Vehicle Auto Insurance Policy",
                    lifecycle_type=LifecycleType.renewal.value,
                    due_date=get_relative_date_str(-4),  # Overdue
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id="group_vehicles",
                    group_name="Shared Vehicle Maintenance",
                    created_at="2026-08-01T08:00:00Z",
                    updated_at="2026-08-01T08:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_2",
                    name="International Passport Renewal",
                    lifecycle_type=LifecycleType.renewal.value,
                    due_date=get_relative_date_str(12),  # Upcoming
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id=None,
                    group_name=None,
                    created_at="2026-08-05T09:00:00Z",
                    updated_at="2026-08-05T09:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_3",
                    name="Residential Homeowners Insurance",
                    lifecycle_type=LifecycleType.renewal.value,
                    due_date=get_relative_date_str(24),  # Upcoming
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id="group_home",
                    group_name="Oakridge Family & Home",
                    created_at="2026-08-10T11:00:00Z",
                    updated_at="2026-08-10T11:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_4",
                    name="State Driver License Renewal",
                    lifecycle_type=LifecycleType.renewal.value,
                    due_date=get_relative_date_str(-30),
                    status=ItemStatus.completed.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id=None,
                    group_name=None,
                    created_at="2026-07-01T10:00:00Z",
                    updated_at="2026-09-01T10:00:00Z",
                ),
                # Maintenance
                LifecycleItemModel(
                    id="item_5",
                    name="HVAC Air Filter & Coil Servicing",
                    lifecycle_type=LifecycleType.maintenance.value,
                    due_date=get_relative_date_str(-2),  # Overdue
                    status=ItemStatus.active.value,
                    owner_id="user_sarah",
                    owner_email="sarah@example.com",
                    group_id="group_home",
                    group_name="Oakridge Family & Home",
                    created_at="2026-08-15T12:00:00Z",
                    updated_at="2026-08-15T12:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_6",
                    name="Honda CR-V Brake Inspection & Tire Rotation",
                    lifecycle_type=LifecycleType.maintenance.value,
                    due_date=get_relative_date_str(9),  # Upcoming
                    status=ItemStatus.active.value,
                    owner_id="user_sarah",
                    owner_email="sarah@example.com",
                    group_id="group_vehicles",
                    group_name="Shared Vehicle Maintenance",
                    created_at="2026-08-20T14:30:00Z",
                    updated_at="2026-08-20T14:30:00Z",
                ),
                LifecycleItemModel(
                    id="item_7",
                    name="Reverse Osmosis Filter Cartridge Replacement",
                    lifecycle_type=LifecycleType.maintenance.value,
                    due_date=None,  # Missing due date allowed
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id="group_home",
                    group_name="Oakridge Family & Home",
                    created_at="2026-09-01T09:00:00Z",
                    updated_at="2026-09-01T09:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_8",
                    name="Annual Water Heater Flush",
                    lifecycle_type=LifecycleType.maintenance.value,
                    due_date=get_relative_date_str(-60),
                    status=ItemStatus.completed.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id="group_home",
                    group_name="Oakridge Family & Home",
                    created_at="2026-06-01T08:00:00Z",
                    updated_at="2026-07-15T08:00:00Z",
                ),
                # Warranties
                LifecycleItemModel(
                    id="item_9",
                    name="MacBook Pro AppleCare+ Protection",
                    lifecycle_type=LifecycleType.warranty.value,
                    due_date=get_relative_date_str(5),  # Upcoming
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id=None,
                    group_name=None,
                    created_at="2026-08-25T15:00:00Z",
                    updated_at="2026-08-25T15:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_10",
                    name='Samsung 65" OLED TV 3-Year Limited Warranty',
                    lifecycle_type=LifecycleType.warranty.value,
                    due_date=get_relative_date_str(-10),  # Overdue
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id="group_home",
                    group_name="Oakridge Family & Home",
                    created_at="2026-07-10T16:00:00Z",
                    updated_at="2026-07-10T16:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_11",
                    name="Bosch Dishwasher 5-Year Parts Warranty",
                    lifecycle_type=LifecycleType.warranty.value,
                    due_date=get_relative_date_str(120),  # Future / Normal
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id="group_home",
                    group_name="Oakridge Family & Home",
                    created_at="2026-08-01T11:00:00Z",
                    updated_at="2026-08-01T11:00:00Z",
                ),
                LifecycleItemModel(
                    id="item_12",
                    name="Espresso Machine Manufacturer Warranty",
                    lifecycle_type=LifecycleType.warranty.value,
                    due_date=None,  # Missing date allowed
                    status=ItemStatus.active.value,
                    owner_id="user_alex",
                    owner_email="alex@example.com",
                    group_id=None,
                    group_name=None,
                    created_at="2026-09-02T13:00:00Z",
                    updated_at="2026-09-02T13:00:00Z",
                ),
            ]
            session.add_all(seed_items)
            session.commit()

    # ---------------- USER METHODS ----------------

    def get_default_user(self) -> UserInDB:
        with self.get_session() as session:
            alex = session.query(UserModel).filter(UserModel.id == "user_alex").first()
            if alex:
                return alex.to_user_in_db()
            first_user = session.query(UserModel).first()
            if first_user:
                return first_user.to_user_in_db()
            # Fallback user if empty
            u = UserModel(
                id="user_alex",
                email="alex@example.com",
                name="Alex Taylor",
                created_at=get_current_iso_time(),
                hashed_password="",
            )
            session.add(u)
            session.commit()
            return u.to_user_in_db()

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        with self.get_session() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            return user.to_user_in_db() if user else None

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        clean = email.strip().lower()
        with self.get_session() as session:
            user = session.query(UserModel).filter(func.lower(UserModel.email) == clean).first()
            return user.to_user_in_db() if user else None

    def create_user(self, email: str, name: str, hashed_password: str) -> UserInDB:
        user_id = str(uuid.uuid4())
        new_user = UserModel(
            id=user_id,
            email=email.strip().lower(),
            name=name.strip(),
            created_at=get_current_iso_time(),
            hashed_password=hashed_password,
        )
        with self.get_session() as session:
            session.add(new_user)
            session.commit()
            return new_user.to_user_in_db()

    def list_users(self) -> List[User]:
        with self.get_session() as session:
            users = session.query(UserModel).all()
            return [u.to_user() for u in users]

    def delete_user(self, user_id: str) -> bool:
        """
        Decision 23 & 30:
        Account deletion deletes everything associated with the account, including its group items.
        - Deletes user
        - Deletes user's personal items
        - Deletes groups owned by user and all items in those groups
        - Removes user email from member list of other groups
        """
        with self._lock, self.get_session() as session:
            target_user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if not target_user:
                return False

            user_email_lower = target_user.email.lower()

            # Find groups owned by user
            owned_groups = session.query(GroupModel.id).filter(GroupModel.owner_id == user_id).all()
            owned_group_ids = [g[0] for g in owned_groups]

            # Delete items owned by user or inside user's owned groups
            if owned_group_ids:
                session.query(LifecycleItemModel).filter(
                    or_(
                        LifecycleItemModel.owner_id == user_id,
                        LifecycleItemModel.group_id.in_(owned_group_ids),
                    )
                ).delete(synchronize_session=False)
            else:
                session.query(LifecycleItemModel).filter(
                    LifecycleItemModel.owner_id == user_id
                ).delete(synchronize_session=False)

            # Delete groups owned by user (cascade deletes their group_members)
            session.query(GroupMemberModel).filter(
                GroupMemberModel.group_id.in_(owned_group_ids)
            ).delete(synchronize_session=False)
            session.query(GroupModel).filter(GroupModel.owner_id == user_id).delete(synchronize_session=False)

            # Remove email from remaining groups
            session.query(GroupMemberModel).filter(
                func.lower(GroupMemberModel.email) == user_email_lower
            ).delete(synchronize_session=False)

            # Delete the user record
            session.delete(target_user)
            session.commit()
            return True

    # ---------------- ITEM METHODS ----------------

    def get_items(
        self,
        user: User,
        group_id: Optional[str] = None,
        lifecycle_type: Optional[LifecycleType] = None,
        search_query: Optional[str] = None,
    ) -> List[LifecycleItem]:
        with self.get_session() as session:
            user_email_lower = user.email.lower()
            # Single-query accessibility filter:
            # Personal items owned by user OR group items where user is member
            group_subquery = (
                session.query(GroupMemberModel.group_id)
                .filter(func.lower(GroupMemberModel.email) == user_email_lower)
                .scalar_subquery()
            )
            accessibility_filter = or_(
                and_(LifecycleItemModel.group_id.is_(None), LifecycleItemModel.owner_id == user.id),
                LifecycleItemModel.group_id.in_(group_subquery),
            )

            query = session.query(LifecycleItemModel).filter(accessibility_filter)

            # Group filter
            if group_id is not None:
                if group_id == "null":
                    query = query.filter(LifecycleItemModel.group_id.is_(None))
                else:
                    query = query.filter(LifecycleItemModel.group_id == group_id)

            # Lifecycle type filter
            if lifecycle_type is not None:
                type_val = lifecycle_type.value if hasattr(lifecycle_type, "value") else str(lifecycle_type)
                query = query.filter(LifecycleItemModel.lifecycle_type == type_val)

            # Search query filter
            if search_query and search_query.strip():
                q = f"%{search_query.strip().lower()}%"
                query = query.filter(
                    or_(
                        func.lower(LifecycleItemModel.name).like(q),
                        func.lower(LifecycleItemModel.group_name).like(q),
                    )
                )

            item_models = query.all()
            accessible_items = [im.to_lifecycle_item() for im in item_models]

            # Sorting: Overdue (1) -> Upcoming (2) -> Normal (3) -> No date (4) -> Completed (5)
            today_str = get_today_date_str()

            def urgency_rank(itm: LifecycleItem) -> int:
                urg = get_item_urgency(itm, today_str)
                if urg == ItemUrgency.overdue:
                    return 1
                if urg == ItemUrgency.upcoming:
                    return 2
                if urg == ItemUrgency.normal:
                    return 3
                if urg == ItemUrgency.no_date:
                    return 4
                return 5  # completed

            def sort_key(itm: LifecycleItem):
                rank = urgency_rank(itm)
                due = itm.dueDate or "9999-99-99"
                return (rank, due, itm.createdAt)

            accessible_items.sort(key=sort_key)
            return accessible_items

    def get_item_by_id(self, item_id: str) -> Optional[LifecycleItem]:
        with self.get_session() as session:
            item = session.query(LifecycleItemModel).filter(LifecycleItemModel.id == item_id).first()
            return item.to_lifecycle_item() if item else None

    def create_item(self, user: User, data: CreateItemDTO) -> LifecycleItem:
        with self.get_session() as session:
            group_name = None
            if data.groupId:
                group = session.query(GroupModel).filter(GroupModel.id == data.groupId).first()
                if not group:
                    raise ValueError("Target group not found")
                user_email_lower = user.email.lower()
                is_member = (
                    session.query(GroupMemberModel)
                    .filter(
                        GroupMemberModel.group_id == data.groupId,
                        func.lower(GroupMemberModel.email) == user_email_lower,
                    )
                    .first()
                ) is not None
                if not is_member:
                    raise PermissionError("Not authorized to add items to this group")
                group_name = group.name

            item_id = str(uuid.uuid4())
            now_iso = get_current_iso_time()
            status_val = (
                (data.status.value if hasattr(data.status, "value") else data.status)
                if data.status
                else ItemStatus.active.value
            )
            type_val = (
                data.lifecycleType.value
                if hasattr(data.lifecycleType, "value")
                else str(data.lifecycleType)
            )

            # Parse due date (supporting ISO 8601 strings from API clients)
            clean_due = None
            if data.dueDate:
                raw_due = data.dueDate.strip()
                if "T" in raw_due:
                    due_dt = datetime.fromisoformat(raw_due)
                else:
                    due_dt = datetime.strptime(raw_due[:10], "%Y-%m-%d")

                # Check if item is already overdue upon creation to evaluate urgency
                now_dt = datetime.now(timezone.utc) if due_dt.tzinfo else datetime.now()
                if due_dt < now_dt:
                    pass

                clean_due = due_dt.strftime("%Y-%m-%d")

            new_item = LifecycleItemModel(
                id=item_id,
                name=data.name.strip(),
                lifecycle_type=type_val,
                due_date=clean_due,
                status=status_val,
                owner_id=user.id,
                owner_email=user.email,
                group_id=data.groupId,
                group_name=group_name,
                created_at=now_iso,
                updated_at=now_iso,
            )
            session.add(new_item)
            session.commit()
            return new_item.to_lifecycle_item()

    def update_item(self, user: User, item_id: str, data: UpdateItemDTO) -> Optional[LifecycleItem]:
        with self.get_session() as session:
            item = session.query(LifecycleItemModel).filter(LifecycleItemModel.id == item_id).first()
            if not item:
                return None

            user_email_lower = user.email.lower()
            if item.group_id:
                is_member = (
                    session.query(GroupMemberModel)
                    .filter(
                        GroupMemberModel.group_id == item.group_id,
                        func.lower(GroupMemberModel.email) == user_email_lower,
                    )
                    .first()
                ) is not None
                if not is_member:
                    raise PermissionError("Not authorized to edit this shared item")
            elif item.owner_id != user.id:
                raise PermissionError("Not authorized to edit this item")

            target_group_id = item.group_id
            target_group_name = item.group_name

            if data.groupId is not None:
                if data.groupId == "" or data.groupId == "null":
                    target_group_id = None
                    target_group_name = None
                else:
                    new_group = session.query(GroupModel).filter(GroupModel.id == data.groupId).first()
                    if not new_group:
                        raise ValueError("Target group not found")
                    is_member_new = (
                        session.query(GroupMemberModel)
                        .filter(
                            GroupMemberModel.group_id == new_group.id,
                            func.lower(GroupMemberModel.email) == user_email_lower,
                        )
                        .first()
                    ) is not None
                    if not is_member_new:
                        raise PermissionError("Not authorized to assign item to this group")
                    target_group_id = new_group.id
                    target_group_name = new_group.name

            if data.name is not None:
                item.name = data.name.strip()
            if data.lifecycleType is not None:
                item.lifecycle_type = (
                    data.lifecycleType.value
                    if hasattr(data.lifecycleType, "value")
                    else str(data.lifecycleType)
                )
            if data.dueDate is not None:
                if data.dueDate == "":
                    item.due_date = None
                elif data.dueDate.strip():
                    raw_due = data.dueDate.strip()
                    if "T" in raw_due:
                        due_dt = datetime.fromisoformat(raw_due)
                    else:
                        due_dt = datetime.strptime(raw_due[:10], "%Y-%m-%d")
                    now_dt = datetime.now(timezone.utc) if due_dt.tzinfo else datetime.now()
                    if due_dt < now_dt:
                        pass
                    item.due_date = due_dt.strftime("%Y-%m-%d")
            if data.status is not None:
                item.status = (
                    data.status.value if hasattr(data.status, "value") else str(data.status)
                )

            item.group_id = target_group_id
            item.group_name = target_group_name
            item.updated_at = get_current_iso_time()
            session.commit()
            return item.to_lifecycle_item()

    def toggle_item_completion(self, item_id: str) -> Optional[LifecycleItem]:
        with self.get_session() as session:
            item = session.query(LifecycleItemModel).filter(LifecycleItemModel.id == item_id).first()
            if not item:
                return None

            new_status = (
                ItemStatus.active.value
                if item.status == ItemStatus.completed.value
                else ItemStatus.completed.value
            )
            item.status = new_status
            item.updated_at = get_current_iso_time()
            session.commit()
            return item.to_lifecycle_item()

    def delete_item(self, user: User, item_id: str) -> bool:
        with self.get_session() as session:
            item = session.query(LifecycleItemModel).filter(LifecycleItemModel.id == item_id).first()
            if not item:
                return False

            user_email_lower = user.email.lower()
            if item.group_id:
                is_member = (
                    session.query(GroupMemberModel)
                    .filter(
                        GroupMemberModel.group_id == item.group_id,
                        func.lower(GroupMemberModel.email) == user_email_lower,
                    )
                    .first()
                ) is not None
                if not is_member:
                    raise PermissionError("Not authorized to delete this shared item")
            elif item.owner_id != user.id:
                raise PermissionError("Not authorized to delete this item")

            session.delete(item)
            session.commit()
            return True

    # ---------------- GROUP METHODS ----------------

    def get_groups(self, user: User) -> List[Group]:
        with self.get_session() as session:
            user_email_lower = user.email.lower()
            groups = (
                session.query(GroupModel)
                .join(GroupMemberModel, GroupModel.id == GroupMemberModel.group_id)
                .filter(func.lower(GroupMemberModel.email) == user_email_lower)
                .distinct()
                .all()
            )
            return [g.to_group() for g in groups]

    def get_group_by_id(self, group_id: str) -> Optional[Group]:
        with self.get_session() as session:
            group = session.query(GroupModel).filter(GroupModel.id == group_id).first()
            return group.to_group() if group else None

    def create_group(self, user: User, name: str) -> Group:
        group_id = str(uuid.uuid4())
        now_iso = get_current_iso_time()
        new_group = GroupModel(
            id=group_id,
            name=name.strip(),
            owner_id=user.id,
            owner_email=user.email,
            created_at=now_iso,
        )
        with self.get_session() as session:
            session.add(new_group)
            session.flush()
            member = GroupMemberModel(group_id=group_id, email=user.email.strip().lower())
            session.add(member)
            session.commit()
            session.refresh(new_group)
            return new_group.to_group()

    def add_member(self, user: User, group_id: str, email: str) -> Optional[Group]:
        with self.get_session() as session:
            group = session.query(GroupModel).filter(GroupModel.id == group_id).first()
            if not group:
                return None

            user_email_lower = user.email.lower()
            is_member = (
                session.query(GroupMemberModel)
                .filter(
                    GroupMemberModel.group_id == group_id,
                    func.lower(GroupMemberModel.email) == user_email_lower,
                )
                .first()
            ) is not None
            if not is_member:
                raise PermissionError("Not authorized to invite members to this group")

            clean_email = email.strip().lower()
            already_member = (
                session.query(GroupMemberModel)
                .filter(
                    GroupMemberModel.group_id == group_id,
                    func.lower(GroupMemberModel.email) == clean_email,
                )
                .first()
            ) is not None
            if not already_member:
                new_member = GroupMemberModel(group_id=group_id, email=clean_email)
                session.add(new_member)
                session.commit()
                session.refresh(group)
            return group.to_group()

    def remove_member(
        self, requester: User, group_id: str, member_email: str
    ) -> Tuple[Optional[Group], Optional[str]]:
        with self.get_session() as session:
            group = session.query(GroupModel).filter(GroupModel.id == group_id).first()
            if not group:
                return None, "Group not found"

            if group.owner_id != requester.id:
                return None, "Only group owner can remove members"

            clean_email = member_email.strip().lower()
            if clean_email == group.owner_email.lower():
                return None, "Cannot remove group owner"

            session.query(GroupMemberModel).filter(
                GroupMemberModel.group_id == group_id,
                func.lower(GroupMemberModel.email) == clean_email,
            ).delete(synchronize_session=False)
            session.commit()
            session.refresh(group)
            return group.to_group(), None

    def leave_group(self, user: User, group_id: str) -> Tuple[bool, Optional[str]]:
        with self.get_session() as session:
            group = session.query(GroupModel).filter(GroupModel.id == group_id).first()
            if not group:
                return False, "Group not found"

            if group.owner_id == user.id:
                return False, "Group owner cannot leave group; delete group instead"

            user_email_lower = user.email.lower()
            session.query(GroupMemberModel).filter(
                GroupMemberModel.group_id == group_id,
                func.lower(GroupMemberModel.email) == user_email_lower,
            ).delete(synchronize_session=False)
            session.commit()
            return True, None

    def delete_group(self, requester: User, group_id: str) -> Tuple[bool, Optional[str]]:
        """
        Decision 30: Deleting a group deletes the group and all its shared items.
        """
        with self._lock, self.get_session() as session:
            group = session.query(GroupModel).filter(GroupModel.id == group_id).first()
            if not group:
                return False, "Group not found"

            if group.owner_id != requester.id:
                return False, "Only group owner can delete group"

            # 1. Cascade delete all items in this group
            session.query(LifecycleItemModel).filter(
                LifecycleItemModel.group_id == group_id
            ).delete(synchronize_session=False)

            # 2. Delete members
            session.query(GroupMemberModel).filter(
                GroupMemberModel.group_id == group_id
            ).delete(synchronize_session=False)

            # 3. Delete group
            session.delete(group)
            session.commit()
            return True, None

    # ---------------- REMINDERS & DIGEST METHODS ----------------

    def get_reminders_summary(self, user: User) -> RemindersSummary:
        items = self.get_items(user)
        today_str = get_today_date_str()

        overdue: List[LifecycleItem] = []
        upcoming: List[LifecycleItem] = []

        for itm in items:
            urg = get_item_urgency(itm, today_str)
            if urg == ItemUrgency.overdue:
                overdue.append(itm)
            elif urg == ItemUrgency.upcoming:
                upcoming.append(itm)

        return RemindersSummary(
            overdue=overdue,
            upcoming=upcoming,
            totalActiveReminders=len(overdue) + len(upcoming),
        )

    def get_digest_config(self) -> DailyDigestConfig:
        with self.get_session() as session:
            cfg = (
                session.query(DailyDigestConfigModel)
                .filter(DailyDigestConfigModel.id == 1)
                .first()
            )
            if not cfg:
                cfg = DailyDigestConfigModel(
                    id=1,
                    time_zone="UTC",
                    delivery_time=DigestDeliveryTime.TIME_08.value,
                    enabled=True,
                )
                session.add(cfg)
                session.commit()
                session.refresh(cfg)
            return cfg.to_digest_config()

    def update_digest_config(self, data: UpdateDigestConfigRequest) -> DailyDigestConfig:
        with self.get_session() as session:
            cfg = (
                session.query(DailyDigestConfigModel)
                .filter(DailyDigestConfigModel.id == 1)
                .first()
            )
            if not cfg:
                cfg = DailyDigestConfigModel(
                    id=1,
                    time_zone="UTC",
                    delivery_time=DigestDeliveryTime.TIME_08.value,
                    enabled=True,
                )
                session.add(cfg)

            if data.timeZone is not None:
                cfg.time_zone = data.timeZone
            if data.deliveryTime is not None:
                cfg.delivery_time = (
                    data.deliveryTime.value
                    if hasattr(data.deliveryTime, "value")
                    else str(data.deliveryTime)
                )
            if data.enabled is not None:
                cfg.enabled = data.enabled

            session.commit()
            session.refresh(cfg)
            return cfg.to_digest_config()

    def generate_digest(self, user: User, recipient_email: Optional[str] = None) -> DailyDigestEmail:
        reminders = self.get_reminders_summary(user)
        target_email = recipient_email or user.email
        today_str = get_today_date_str()
        config = self.get_digest_config()

        total_count = reminders.totalActiveReminders
        if total_count == 0:
            subject = f"[Lifecycle Tracker] All clear for today ({today_str})"
        elif len(reminders.overdue) > 0:
            subject = (
                f"[Action Required] {len(reminders.overdue)} overdue & "
                f"{len(reminders.upcoming)} upcoming lifecycle items"
            )
        else:
            subject = f"[Upcoming Actions] {len(reminders.upcoming)} upcoming lifecycle items"

        # Generate Text lines
        text_lines = [
            "PERSONAL LIFECYCLE TRACKER - DAILY DIGEST",
            f"Generated for: {user.name} ({target_email})",
            f"Date: {today_str} | Scheduled delivery: {config.deliveryTime} ({config.timeZone})",
            "--------------------------------------------------",
            "",
        ]
        if reminders.overdue:
            text_lines.append(f"🔴 OVERDUE ITEMS ({len(reminders.overdue)}):")
            for idx, item in enumerate(reminders.overdue, 1):
                rel = get_relative_due_date_label(item.dueDate, item.status, today_str)
                grp = f" [Group: {item.groupName}]" if item.groupName else " [Personal]"
                text_lines.append(f"  {idx}. [{item.lifecycleType.upper()}] {item.name}")
                text_lines.append(f"     Due: {format_display_date(item.dueDate)} ({rel}){grp}")
            text_lines.append("")

        if reminders.upcoming:
            text_lines.append(f"🟡 UPCOMING ITEMS ({len(reminders.upcoming)}):")
            for idx, item in enumerate(reminders.upcoming, 1):
                rel = get_relative_due_date_label(item.dueDate, item.status, today_str)
                grp = f" [Group: {item.groupName}]" if item.groupName else " [Personal]"
                text_lines.append(f"  {idx}. [{item.lifecycleType.upper()}] {item.name}")
                text_lines.append(f"     Due: {format_display_date(item.dueDate)} ({rel}){grp}")
            text_lines.append("")

        if total_count == 0:
            text_lines.append("You have zero overdue or upcoming items scheduled for the next 30 days.")
            text_lines.append("")

        text_lines.append("--------------------------------------------------")
        text_lines.append("Delivered automatically by your Daily Digest schedule.")
        text_lines.append("Note: Reminder channels are always active.")

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="font-family: sans-serif; background-color: #f8fafc; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 24px;">
    <h2>Personal Lifecycle Tracker</h2>
    <p style="color: #64748b;">Daily Digest for {user.name} &bull; {today_str} &bull; {config.deliveryTime} ({config.timeZone})</p>
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;" />
    <h3>{subject}</h3>
    <p>Overdue items: {len(reminders.overdue)} | Upcoming items: {len(reminders.upcoming)}</p>
  </div>
</body>
</html>"""

        digest_id = f"digest_{int(datetime.now(timezone.utc).timestamp())}_{str(uuid.uuid4())[:6]}"
        now_iso = get_current_iso_time()

        history_model = DailyDigestHistoryModel(
            id=digest_id,
            recipient_email=target_email,
            recipient_name=user.name,
            generated_at=now_iso,
            delivery_time=config.deliveryTime.value if hasattr(config.deliveryTime, "value") else str(config.deliveryTime),
            time_zone=config.timeZone,
            subject=subject,
            overdue_count=len(reminders.overdue),
            upcoming_count=len(reminders.upcoming),
            overdue_items=json.dumps([it.model_dump() for it in reminders.overdue]),
            upcoming_items=json.dumps([it.model_dump() for it in reminders.upcoming]),
            html_content=html_content,
            text_content="\n".join(text_lines),
        )

        with self.get_session() as session:
            session.add(history_model)
            session.commit()

            # Retain only the 20 most recent entries
            extra_ids = [
                row[0]
                for row in session.query(DailyDigestHistoryModel.id)
                .order_by(DailyDigestHistoryModel.pk.desc())
                .offset(20)
                .all()
            ]
            if extra_ids:
                session.query(DailyDigestHistoryModel).filter(
                    DailyDigestHistoryModel.id.in_(extra_ids)
                ).delete(synchronize_session=False)
                session.commit()

            return history_model.to_digest_email()

    def get_digest_history(self) -> List[DailyDigestEmail]:
        with self.get_session() as session:
            records = (
                session.query(DailyDigestHistoryModel)
                .order_by(DailyDigestHistoryModel.pk.desc())
                .limit(20)
                .all()
            )
            return [r.to_digest_email() for r in records]

    def sync_metrics(self) -> None:
        try:
            from app.telemetry import update_lifecycle_items_gauge
            with self.get_session() as session:
                rows = (
                    session.query(
                        LifecycleItemModel.lifecycle_type,
                        LifecycleItemModel.status,
                        func.count(LifecycleItemModel.id),
                    )
                    .group_by(LifecycleItemModel.lifecycle_type, LifecycleItemModel.status)
                    .all()
                )
                for l_type, status_val, cnt in rows:
                    update_lifecycle_items_gauge(lifecycle_type=str(l_type), status=str(status_val), count=int(cnt))
        except Exception:
            pass


# Aliases for backwards compatibility
Store = DatabaseStore
SQLAlchemyStore = DatabaseStore
InMemoryStore = DatabaseStore

# Global singleton instance
_store_instance: Optional[DatabaseStore] = None


def get_store() -> DatabaseStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = DatabaseStore()
    return _store_instance


def reset_store(database_url: Optional[str] = None) -> DatabaseStore:
    global _store_instance
    _store_instance = DatabaseStore(database_url=database_url)
    return _store_instance
