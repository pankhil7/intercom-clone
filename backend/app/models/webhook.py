import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    secret = Column(String(255), nullable=False)
    events = Column(ARRAY(String), default=[])
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")
