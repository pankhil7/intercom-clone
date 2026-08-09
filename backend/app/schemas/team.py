from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator


class InviteRequest(BaseModel):
    email: str
    role: str = "agent"


class AcceptInviteRequest(BaseModel):
    token: str
    full_name: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class ValidateInviteResponse(BaseModel):
    email: str
    role: str
    organization_name: str


class MemberResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_seen_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class InvitationResponse(BaseModel):
    id: UUID
    email: str
    role: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
