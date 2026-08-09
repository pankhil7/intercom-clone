import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Inbox(Base):
    __tablename__ = "inboxes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)  # chat | email — exposed as 'channel' on API
    channel_type = Column(String(50), nullable=True)  # legacy alias, kept for compat
    email_address = Column(String(255), nullable=True)
    widget_key = Column(String(64), nullable=True, unique=True)
    widget_color = Column(String(7), default="#6366f1")
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="inboxes")
    conversations = relationship("Conversation", back_populates="inbox")
