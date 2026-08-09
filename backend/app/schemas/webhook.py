from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class WebhookCreate(BaseModel):
    url: str
    events: List[str]
    secret: Optional[str] = None


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: UUID
    url: str
    events: List[str]
    is_active: bool
    last_triggered_at: Optional[datetime] = None
    failure_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DeliveryResponse(BaseModel):
    id: UUID
    event_type: str
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    duration_ms: Optional[int] = None
    attempt_count: int
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
