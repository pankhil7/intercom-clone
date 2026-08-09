from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator


class SignupRequest(BaseModel):
    organization_name: str
    email: str
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    organization_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    widget_color: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserResponse
    organization: OrganizationResponse
