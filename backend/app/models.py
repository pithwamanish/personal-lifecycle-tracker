from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class HealthStatus(BaseModel):
    status: str = "healthy"
    database: str = "connected"
    version: str = "1.0.0"


class LifecycleType(str, Enum):
    renewal = "renewal"
    maintenance = "maintenance"
    warranty = "warranty"


class ItemStatus(str, Enum):
    active = "active"
    completed = "completed"


class ItemUrgency(str, Enum):
    overdue = "overdue"
    upcoming = "upcoming"
    normal = "normal"
    no_date = "no_date"
    completed = "completed"


class DigestDeliveryTime(str, Enum):
    TIME_06 = "06:00"
    TIME_08 = "08:00"
    TIME_09 = "09:00"
    TIME_12 = "12:00"


class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    createdAt: str

    model_config = ConfigDict(populate_by_name=True)


class UserInDB(User):
    hashed_password: str


class AuthResponse(BaseModel):
    user: User
    token: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LifecycleItem(BaseModel):
    id: str
    name: str
    lifecycleType: LifecycleType
    dueDate: Optional[str] = None
    status: ItemStatus
    ownerId: str
    ownerEmail: EmailStr
    groupId: Optional[str] = None
    groupName: Optional[str] = None
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(populate_by_name=True)


class CreateItemDTO(BaseModel):
    name: str
    lifecycleType: LifecycleType
    dueDate: Optional[str] = None
    status: Optional[ItemStatus] = ItemStatus.active
    groupId: Optional[str] = None


class UpdateItemDTO(BaseModel):
    name: Optional[str] = None
    lifecycleType: Optional[LifecycleType] = None
    dueDate: Optional[str] = None
    status: Optional[ItemStatus] = None
    groupId: Optional[str] = None


class Group(BaseModel):
    id: str
    name: str
    ownerId: str
    ownerEmail: EmailStr
    memberEmails: List[EmailStr]
    createdAt: str

    model_config = ConfigDict(populate_by_name=True)


class CreateGroupRequest(BaseModel):
    name: str


class AddMemberRequest(BaseModel):
    email: EmailStr


class DailyDigestConfig(BaseModel):
    timeZone: str = "UTC"
    deliveryTime: DigestDeliveryTime = DigestDeliveryTime.TIME_08
    enabled: bool = True

    model_config = ConfigDict(populate_by_name=True)


class UpdateDigestConfigRequest(BaseModel):
    timeZone: Optional[str] = None
    deliveryTime: Optional[DigestDeliveryTime] = None
    enabled: Optional[bool] = None


class DailyDigestEmail(BaseModel):
    id: str
    recipientEmail: EmailStr
    recipientName: str
    generatedAt: str
    deliveryTime: DigestDeliveryTime
    timeZone: str
    subject: str
    overdueCount: int
    upcomingCount: int
    overdueItems: List[LifecycleItem]
    upcomingItems: List[LifecycleItem]
    htmlContent: str
    textContent: str

    model_config = ConfigDict(populate_by_name=True)


class GenerateDigestRequest(BaseModel):
    recipientEmail: Optional[EmailStr] = None


class RemindersSummary(BaseModel):
    overdue: List[LifecycleItem]
    upcoming: List[LifecycleItem]
    totalActiveReminders: int


class ErrorResponse(BaseModel):
    error: str


class MessageResponse(BaseModel):
    message: str
