from __future__ import annotations

import json
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models import (
    DailyDigestConfig,
    DailyDigestEmail,
    DigestDeliveryTime,
    Group,
    ItemStatus,
    LifecycleItem,
    LifecycleType,
    User,
    UserInDB,
)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(String(64), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    def to_user(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            createdAt=self.created_at,
        )

    def to_user_in_db(self) -> UserInDB:
        return UserInDB(
            id=self.id,
            email=self.email,
            name=self.name,
            createdAt=self.created_at,
            hashed_password=self.hashed_password,
        )


class GroupModel(Base):
    __tablename__ = "groups"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_email = Column(String(255), nullable=False)
    created_at = Column(String(64), nullable=False)

    members = relationship(
        "GroupMemberModel",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="GroupMemberModel.id",
    )

    def to_group(self) -> Group:
        return Group(
            id=self.id,
            name=self.name,
            ownerId=self.owner_id,
            ownerEmail=self.owner_email,
            memberEmails=[m.email for m in self.members],
            createdAt=self.created_at,
        )


class GroupMemberModel(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(64), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)

    group = relationship("GroupModel", back_populates="members")

    __table_args__ = (
        UniqueConstraint("group_id", "email", name="uq_group_member"),
    )


class LifecycleItemModel(Base):
    __tablename__ = "items"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    lifecycle_type = Column(String(32), nullable=False, index=True)
    due_date = Column(String(32), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)
    owner_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_email = Column(String(255), nullable=False)
    group_id = Column(String(64), ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True)
    group_name = Column(String(255), nullable=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    def to_lifecycle_item(self) -> LifecycleItem:
        return LifecycleItem(
            id=self.id,
            name=self.name,
            lifecycleType=LifecycleType(self.lifecycle_type),
            dueDate=self.due_date,
            status=ItemStatus(self.status),
            ownerId=self.owner_id,
            ownerEmail=self.owner_email,
            groupId=self.group_id,
            groupName=self.group_name,
            createdAt=self.created_at,
            updatedAt=self.updated_at,
        )


class DailyDigestConfigModel(Base):
    __tablename__ = "daily_digest_config"

    id = Column(Integer, primary_key=True, default=1)
    time_zone = Column(String(64), nullable=False, default="UTC")
    delivery_time = Column(String(16), nullable=False, default="08:00")
    enabled = Column(Boolean, nullable=False, default=True)

    def to_digest_config(self) -> DailyDigestConfig:
        return DailyDigestConfig(
            timeZone=self.time_zone,
            deliveryTime=DigestDeliveryTime(self.delivery_time),
            enabled=self.enabled,
        )


class DailyDigestHistoryModel(Base):
    __tablename__ = "daily_digest_history"

    pk = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(64), unique=True, index=True, nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    generated_at = Column(String(64), nullable=False, index=True)
    delivery_time = Column(String(16), nullable=False)
    time_zone = Column(String(64), nullable=False)
    subject = Column(String(255), nullable=False)
    overdue_count = Column(Integer, nullable=False, default=0)
    upcoming_count = Column(Integer, nullable=False, default=0)
    overdue_items = Column(Text, nullable=False)
    upcoming_items = Column(Text, nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=False)

    def to_digest_email(self) -> DailyDigestEmail:
        try:
            overdue_raw = json.loads(self.overdue_items)
            upcoming_raw = json.loads(self.upcoming_items)
            overdue_list = [LifecycleItem.model_validate(it) for it in overdue_raw]
            upcoming_list = [LifecycleItem.model_validate(it) for it in upcoming_raw]
        except Exception:
            overdue_list = []
            upcoming_list = []

        return DailyDigestEmail(
            id=self.id,
            recipientEmail=self.recipient_email,
            recipientName=self.recipient_name,
            generatedAt=self.generated_at,
            deliveryTime=DigestDeliveryTime(self.delivery_time),
            timeZone=self.time_zone,
            subject=self.subject,
            overdueCount=self.overdue_count,
            upcomingCount=self.upcoming_count,
            overdueItems=overdue_list,
            upcomingItems=upcoming_list,
            htmlContent=self.html_content,
            textContent=self.text_content,
        )
