from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    contact_id: Optional[UUID] = None
    channel: str
    subject: Optional[str] = None
    inbox_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None


class ConversationUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    snoozed_until: Optional[datetime] = None
    subject: Optional[str] = None
    sla_policy_id: Optional[UUID] = None


class MessageCreate(BaseModel):
    content: str
    content_type: str = "text"


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    sender_id: Optional[UUID] = None
    content: str
    content_type: str
    attachments: Any = []
    email_message_id: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactMini(BaseModel):
    id: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    avatar: None = None

    model_config = {"from_attributes": True}


class AssigneeMini(BaseModel):
    id: UUID
    full_name: str
    email: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    id: UUID
    status: str
    channel: str
    subject: Optional[str] = None
    contact: Optional[ContactMini] = None
    assignee: Optional[AssigneeMini] = None
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    sla_breach: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: UUID
    status: str
    channel: str
    subject: Optional[str] = None
    contact: Optional[ContactMini] = None
    assignee: Optional[AssigneeMini] = None
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    sla_breach: bool = False
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}
