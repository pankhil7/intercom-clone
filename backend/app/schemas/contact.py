from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel


class ContactCreate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    external_id: Optional[str] = None
    custom_attributes: Dict[str, Any] = {}


class ContactUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    external_id: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None


class ContactResponse(BaseModel):
    id: UUID
    organization_id: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    external_id: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    timezone: Optional[str] = None
    location: Any = {}
    custom_attributes: Any = {}
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
