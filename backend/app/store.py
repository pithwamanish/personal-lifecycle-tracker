from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

from app.auth import hash_password
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


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.users: Dict[str, UserInDB] = {}
        self.groups: Dict[str, Group] = {}
        self.items: Dict[str, LifecycleItem] = {}
        self.digest_config: DailyDigestConfig = DailyDigestConfig()
        self.digest_history: List[DailyDigestEmail] = []
        self.seed()

    def seed(self) -> None:
        """Seed the in-memory store with default users, groups, and items."""
        with self._lock:
            self.users.clear()
            self.groups.clear()
            self.items.clear()
            self.digest_history.clear()
            self.digest_config = DailyDigestConfig(
                timeZone="UTC",
                deliveryTime=DigestDeliveryTime.TIME_08,
                enabled=True,
            )

            # Seed Users
            default_password_hash = hash_password("password123")
            users_data = [
                UserInDB(
                    id="user_alex",
                    email="alex@example.com",
                    name="Alex Taylor",
                    createdAt="2026-01-10T08:00:00Z",
                    hashed_password=default_password_hash,
                ),
                UserInDB(
                    id="user_sarah",
                    email="sarah@example.com",
                    name="Sarah Jenkins",
                    createdAt="2026-02-14T09:30:00Z",
                    hashed_password=default_password_hash,
                ),
                UserInDB(
                    id="user_jordan",
                    email="jordan@example.com",
                    name="Jordan Patel",
                    createdAt="2026-03-01T11:15:00Z",
                    hashed_password=default_password_hash,
                ),
            ]
            for u in users_data:
                self.users[u.id] = u

            # Seed Groups
            groups_data = [
                Group(
                    id="group_home",
                    name="Oakridge Family & Home",
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    memberEmails=["alex@example.com", "sarah@example.com"],
                    createdAt="2026-02-15T10:00:00Z",
                ),
                Group(
                    id="group_vehicles",
                    name="Shared Vehicle Maintenance",
                    ownerId="user_sarah",
                    ownerEmail="sarah@example.com",
                    memberEmails=["sarah@example.com", "alex@example.com", "jordan@example.com"],
                    createdAt="2026-02-20T14:00:00Z",
                ),
            ]
            for g in groups_data:
                self.groups[g.id] = g

            # Seed Items (12 items matching the frontend seed dataset)
            seed_items = [
                # Renewals
                LifecycleItem(
                    id="item_1",
                    name="Vehicle Auto Insurance Policy",
                    lifecycleType=LifecycleType.renewal,
                    dueDate=get_relative_date_str(-4),  # Overdue
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId="group_vehicles",
                    groupName="Shared Vehicle Maintenance",
                    createdAt="2026-08-01T08:00:00Z",
                    updatedAt="2026-08-01T08:00:00Z",
                ),
                LifecycleItem(
                    id="item_2",
                    name="International Passport Renewal",
                    lifecycleType=LifecycleType.renewal,
                    dueDate=get_relative_date_str(12),  # Upcoming
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId=None,
                    groupName=None,
                    createdAt="2026-08-05T09:00:00Z",
                    updatedAt="2026-08-05T09:00:00Z",
                ),
                LifecycleItem(
                    id="item_3",
                    name="Residential Homeowners Insurance",
                    lifecycleType=LifecycleType.renewal,
                    dueDate=get_relative_date_str(24),  # Upcoming
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId="group_home",
                    groupName="Oakridge Family & Home",
                    createdAt="2026-08-10T11:00:00Z",
                    updatedAt="2026-08-10T11:00:00Z",
                ),
                LifecycleItem(
                    id="item_4",
                    name="State Driver License Renewal",
                    lifecycleType=LifecycleType.renewal,
                    dueDate=get_relative_date_str(-30),
                    status=ItemStatus.completed,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId=None,
                    groupName=None,
                    createdAt="2026-07-01T10:00:00Z",
                    updatedAt="2026-09-01T10:00:00Z",
                ),
                # Maintenance
                LifecycleItem(
                    id="item_5",
                    name="HVAC Air Filter & Coil Servicing",
                    lifecycleType=LifecycleType.maintenance,
                    dueDate=get_relative_date_str(-2),  # Overdue
                    status=ItemStatus.active,
                    ownerId="user_sarah",
                    ownerEmail="sarah@example.com",
                    groupId="group_home",
                    groupName="Oakridge Family & Home",
                    createdAt="2026-08-15T12:00:00Z",
                    updatedAt="2026-08-15T12:00:00Z",
                ),
                LifecycleItem(
                    id="item_6",
                    name="Honda CR-V Brake Inspection & Tire Rotation",
                    lifecycleType=LifecycleType.maintenance,
                    dueDate=get_relative_date_str(9),  # Upcoming
                    status=ItemStatus.active,
                    ownerId="user_sarah",
                    ownerEmail="sarah@example.com",
                    groupId="group_vehicles",
                    groupName="Shared Vehicle Maintenance",
                    createdAt="2026-08-20T14:30:00Z",
                    updatedAt="2026-08-20T14:30:00Z",
                ),
                LifecycleItem(
                    id="item_7",
                    name="Reverse Osmosis Filter Cartridge Replacement",
                    lifecycleType=LifecycleType.maintenance,
                    dueDate=None,  # Missing due date allowed
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId="group_home",
                    groupName="Oakridge Family & Home",
                    createdAt="2026-09-01T09:00:00Z",
                    updatedAt="2026-09-01T09:00:00Z",
                ),
                LifecycleItem(
                    id="item_8",
                    name="Annual Water Heater Flush",
                    lifecycleType=LifecycleType.maintenance,
                    dueDate=get_relative_date_str(-60),
                    status=ItemStatus.completed,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId="group_home",
                    groupName="Oakridge Family & Home",
                    createdAt="2026-06-01T08:00:00Z",
                    updatedAt="2026-07-15T08:00:00Z",
                ),
                # Warranties
                LifecycleItem(
                    id="item_9",
                    name="MacBook Pro AppleCare+ Protection",
                    lifecycleType=LifecycleType.warranty,
                    dueDate=get_relative_date_str(5),  # Upcoming
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId=None,
                    groupName=None,
                    createdAt="2026-08-25T15:00:00Z",
                    updatedAt="2026-08-25T15:00:00Z",
                ),
                LifecycleItem(
                    id="item_10",
                    name='Samsung 65" OLED TV 3-Year Limited Warranty',
                    lifecycleType=LifecycleType.warranty,
                    dueDate=get_relative_date_str(-10),  # Overdue
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId="group_home",
                    groupName="Oakridge Family & Home",
                    createdAt="2026-07-10T16:00:00Z",
                    updatedAt="2026-07-10T16:00:00Z",
                ),
                LifecycleItem(
                    id="item_11",
                    name="Bosch Dishwasher 5-Year Parts Warranty",
                    lifecycleType=LifecycleType.warranty,
                    dueDate=get_relative_date_str(120),  # Future / Normal
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId="group_home",
                    groupName="Oakridge Family & Home",
                    createdAt="2026-08-01T11:00:00Z",
                    updatedAt="2026-08-01T11:00:00Z",
                ),
                LifecycleItem(
                    id="item_12",
                    name="Espresso Machine Manufacturer Warranty",
                    lifecycleType=LifecycleType.warranty,
                    dueDate=None,  # Missing date allowed
                    status=ItemStatus.active,
                    ownerId="user_alex",
                    ownerEmail="alex@example.com",
                    groupId=None,
                    groupName=None,
                    createdAt="2026-09-02T13:00:00Z",
                    updatedAt="2026-09-02T13:00:00Z",
                ),
            ]
            for itm in seed_items:
                self.items[itm.id] = itm

    # ---------------- USER METHODS ----------------

    def get_default_user(self) -> UserInDB:
        with self._lock:
            if "user_alex" in self.users:
                return self.users["user_alex"]
            first_user = next(iter(self.users.values()), None)
            if first_user:
                return first_user
            # Fallback user if empty
            u = UserInDB(
                id="user_alex",
                email="alex@example.com",
                name="Alex Taylor",
                createdAt=get_current_iso_time(),
                hashed_password="",
            )
            self.users[u.id] = u
            return u

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        with self._lock:
            return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        clean = email.strip().lower()
        with self._lock:
            for u in self.users.values():
                if u.email.lower() == clean:
                    return u
            return None

    def create_user(self, email: str, name: str, hashed_password: str) -> UserInDB:
        with self._lock:
            user_id = str(uuid.uuid4())
            new_user = UserInDB(
                id=user_id,
                email=email.strip().lower(),
                name=name.strip(),
                createdAt=get_current_iso_time(),
                hashed_password=hashed_password,
            )
            self.users[new_user.id] = new_user
            return new_user

    def list_users(self) -> List[User]:
        with self._lock:
            return [
                User(id=u.id, email=u.email, name=u.name, createdAt=u.createdAt)
                for u in self.users.values()
            ]

    def delete_user(self, user_id: str) -> bool:
        """
        Decision 23 & 30:
        Account deletion deletes everything associated with the account, including its group items.
        - Deletes user
        - Deletes user's personal items
        - Deletes groups owned by user and all items in those groups
        - Removes user email from member list of other groups
        """
        with self._lock:
            target_user = self.users.get(user_id)
            if not target_user:
                return False

            user_email_lower = target_user.email.lower()

            # Find groups owned by user
            owned_group_ids = {g.id for g in self.groups.values() if g.ownerId == user_id}

            # Delete items owned by user or inside user's owned groups
            self.items = {
                k: itm
                for k, itm in self.items.items()
                if itm.ownerId != user_id and (itm.groupId not in owned_group_ids)
            }

            # Delete groups owned by user
            self.groups = {k: g for k, g in self.groups.items() if g.ownerId != user_id}

            # Remove email from remaining groups
            for g in self.groups.values():
                g.memberEmails = [em for em in g.memberEmails if em.lower() != user_email_lower]

            del self.users[user_id]
            return True

    # ---------------- ITEM METHODS ----------------

    def get_items(
        self,
        user: User,
        group_id: Optional[str] = None,
        lifecycle_type: Optional[LifecycleType] = None,
        search_query: Optional[str] = None,
    ) -> List[LifecycleItem]:
        with self._lock:
            user_email_lower = user.email.lower()
            # Groups user belongs to
            accessible_group_ids = {
                g.id
                for g in self.groups.values()
                if any(em.lower() == user_email_lower for em in g.memberEmails)
            }

            # Filter items accessible to user:
            # 1. Personal items owned by user (groupId is None)
            # 2. Group items where user is a group member
            accessible: List[LifecycleItem] = []
            for item in self.items.values():
                if item.groupId is None:
                    if item.ownerId == user.id:
                        accessible.append(item)
                elif item.groupId in accessible_group_ids:
                    accessible.append(item)

            # Apply group filter
            if group_id is not None:
                if group_id == "null":
                    accessible = [i for i in accessible if i.groupId is None]
                else:
                    accessible = [i for i in accessible if i.groupId == group_id]

            # Apply lifecycle type filter
            if lifecycle_type is not None:
                accessible = [i for i in accessible if i.lifecycleType == lifecycle_type]

            # Apply search query
            if search_query and search_query.strip():
                q = search_query.strip().lower()
                accessible = [
                    i
                    for i in accessible
                    if q in i.name.lower() or (i.groupName and q in i.groupName.lower())
                ]

            # Sorting:
            # Overdue (1) -> Upcoming (2) -> Normal (3) -> No date (4) -> Completed (5)
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

            accessible.sort(key=sort_key)
            return accessible

    def get_item_by_id(self, item_id: str) -> Optional[LifecycleItem]:
        with self._lock:
            return self.items.get(item_id)

    def create_item(self, user: User, data: CreateItemDTO) -> LifecycleItem:
        with self._lock:
            group_name = None
            if data.groupId:
                group = self.groups.get(data.groupId)
                if not group:
                    raise ValueError("Target group not found")
                if not any(em.lower() == user.email.lower() for em in group.memberEmails):
                    raise PermissionError("Not authorized to add items to this group")
                group_name = group.name

            item_id = str(uuid.uuid4())
            now_iso = get_current_iso_time()
            new_item = LifecycleItem(
                id=item_id,
                name=data.name.strip(),
                lifecycleType=data.lifecycleType,
                dueDate=data.dueDate.strip()[:10] if data.dueDate else None,
                status=data.status or ItemStatus.active,
                ownerId=user.id,
                ownerEmail=user.email,
                groupId=data.groupId,
                groupName=group_name,
                createdAt=now_iso,
                updatedAt=now_iso,
            )
            self.items[new_item.id] = new_item
            return new_item

    def update_item(self, user: User, item_id: str, data: UpdateItemDTO) -> Optional[LifecycleItem]:
        with self._lock:
            item = self.items.get(item_id)
            if not item:
                return None

            # Permission check:
            # If personal item: must be owner.
            # If group item: any group member can edit (Decision 14).
            user_email_lower = user.email.lower()
            if item.groupId:
                group = self.groups.get(item.groupId)
                if not group or not any(em.lower() == user_email_lower for em in group.memberEmails):
                    raise PermissionError("Not authorized to edit this shared item")
            elif item.ownerId != user.id:
                raise PermissionError("Not authorized to edit this item")

            target_group_id = item.groupId
            target_group_name = item.groupName

            if data.groupId is not None:
                if data.groupId == "" or data.groupId == "null":
                    target_group_id = None
                    target_group_name = None
                else:
                    new_group = self.groups.get(data.groupId)
                    if not new_group:
                        raise ValueError("Target group not found")
                    if not any(em.lower() == user_email_lower for em in new_group.memberEmails):
                        raise PermissionError("Not authorized to assign item to this group")
                    target_group_id = new_group.id
                    target_group_name = new_group.name

            updated_item = LifecycleItem(
                id=item.id,
                name=data.name.strip() if data.name is not None else item.name,
                lifecycleType=data.lifecycleType if data.lifecycleType is not None else item.lifecycleType,
                dueDate=(
                    data.dueDate.strip()[:10]
                    if (data.dueDate and data.dueDate.strip())
                    else (None if data.dueDate == "" else item.dueDate)
                ),
                status=data.status if data.status is not None else item.status,
                ownerId=item.ownerId,
                ownerEmail=item.ownerEmail,
                groupId=target_group_id,
                groupName=target_group_name,
                createdAt=item.createdAt,
                updatedAt=get_current_iso_time(),
            )
            self.items[item.id] = updated_item
            return updated_item

    def toggle_item_completion(self, item_id: str) -> Optional[LifecycleItem]:
        with self._lock:
            item = self.items.get(item_id)
            if not item:
                return None

            new_status = ItemStatus.active if item.status == ItemStatus.completed else ItemStatus.completed
            updated_item = LifecycleItem(
                id=item.id,
                name=item.name,
                lifecycleType=item.lifecycleType,
                dueDate=item.dueDate,
                status=new_status,
                ownerId=item.ownerId,
                ownerEmail=item.ownerEmail,
                groupId=item.groupId,
                groupName=item.groupName,
                createdAt=item.createdAt,
                updatedAt=get_current_iso_time(),
            )
            self.items[item.id] = updated_item
            return updated_item

    def delete_item(self, user: User, item_id: str) -> bool:
        with self._lock:
            item = self.items.get(item_id)
            if not item:
                return False

            user_email_lower = user.email.lower()
            if item.groupId:
                group = self.groups.get(item.groupId)
                if not group or not any(em.lower() == user_email_lower for em in group.memberEmails):
                    raise PermissionError("Not authorized to delete this shared item")
            elif item.ownerId != user.id:
                raise PermissionError("Not authorized to delete this item")

            del self.items[item_id]
            return True

    # ---------------- GROUP METHODS ----------------

    def get_groups(self, user: User) -> List[Group]:
        with self._lock:
            user_email_lower = user.email.lower()
            return [
                g
                for g in self.groups.values()
                if any(em.lower() == user_email_lower for em in g.memberEmails)
            ]

    def get_group_by_id(self, group_id: str) -> Optional[Group]:
        with self._lock:
            return self.groups.get(group_id)

    def create_group(self, user: User, name: str) -> Group:
        with self._lock:
            group_id = str(uuid.uuid4())
            new_group = Group(
                id=group_id,
                name=name.strip(),
                ownerId=user.id,
                ownerEmail=user.email,
                memberEmails=[user.email],
                createdAt=get_current_iso_time(),
            )
            self.groups[new_group.id] = new_group
            return new_group

    def add_member(self, user: User, group_id: str, email: str) -> Optional[Group]:
        with self._lock:
            group = self.groups.get(group_id)
            if not group:
                return None

            user_email_lower = user.email.lower()
            if not any(em.lower() == user_email_lower for em in group.memberEmails):
                raise PermissionError("Not authorized to invite members to this group")

            clean_email = email.strip().lower()
            if not any(em.lower() == clean_email for em in group.memberEmails):
                group.memberEmails.append(clean_email)
            return group

    def remove_member(
        self, requester: User, group_id: str, member_email: str
    ) -> Tuple[Optional[Group], Optional[str]]:
        with self._lock:
            group = self.groups.get(group_id)
            if not group:
                return None, "Group not found"

            if group.ownerId != requester.id:
                return None, "Only group owner can remove members"

            clean_email = member_email.strip().lower()
            if clean_email == group.ownerEmail.lower():
                return None, "Cannot remove group owner"

            group.memberEmails = [em for em in group.memberEmails if em.lower() != clean_email]
            # Decision 18: Items remain with the group when a member departs
            return group, None

    def leave_group(self, user: User, group_id: str) -> Tuple[bool, Optional[str]]:
        with self._lock:
            group = self.groups.get(group_id)
            if not group:
                return False, "Group not found"

            if group.ownerId == user.id:
                return False, "Group owner cannot leave group; delete group instead"

            user_email_lower = user.email.lower()
            group.memberEmails = [em for em in group.memberEmails if em.lower() != user_email_lower]
            return True, None

    def delete_group(self, requester: User, group_id: str) -> Tuple[bool, Optional[str]]:
        """
        Decision 30: Deleting a group deletes the group and all its shared items.
        """
        with self._lock:
            group = self.groups.get(group_id)
            if not group:
                return False, "Group not found"

            if group.ownerId != requester.id:
                return False, "Only group owner can delete group"

            # 1. Cascade delete all items in this group
            self.items = {k: itm for k, itm in self.items.items() if itm.groupId != group_id}

            # 2. Delete group
            del self.groups[group_id]
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
        with self._lock:
            return self.digest_config

    def update_digest_config(self, data: UpdateDigestConfigRequest) -> DailyDigestConfig:
        with self._lock:
            if data.timeZone is not None:
                self.digest_config.timeZone = data.timeZone
            if data.deliveryTime is not None:
                self.digest_config.deliveryTime = data.deliveryTime
            if data.enabled is not None:
                self.digest_config.enabled = data.enabled
            return self.digest_config

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

        digest = DailyDigestEmail(
            id=f"digest_{int(datetime.now(timezone.utc).timestamp())}_{str(uuid.uuid4())[:6]}",
            recipientEmail=target_email,
            recipientName=user.name,
            generatedAt=get_current_iso_time(),
            deliveryTime=config.deliveryTime,
            timeZone=config.timeZone,
            subject=subject,
            overdueCount=len(reminders.overdue),
            upcomingCount=len(reminders.upcoming),
            overdueItems=reminders.overdue,
            upcomingItems=reminders.upcoming,
            htmlContent=html_content,
            textContent="\n".join(text_lines),
        )

        with self._lock:
            self.digest_history.insert(0, digest)
            if len(self.digest_history) > 20:
                self.digest_history = self.digest_history[:20]

        return digest

    def get_digest_history(self) -> List[DailyDigestEmail]:
        with self._lock:
            return list(self.digest_history)


# Global singleton instance
_store_instance = InMemoryStore()


def get_store() -> InMemoryStore:
    return _store_instance
