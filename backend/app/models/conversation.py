import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    inbox_id = Column(UUID(as_uuid=True), ForeignKey("inboxes.id", ondelete="SET NULL"), nullable=True)
    channel = Column(String(50), nullable=False)  # chat | email
    status = Column(String(50), nullable=False, default="open", index=True)  # open | snoozed | resolved
    subject = Column(Text, nullable=True)
    snoozed_until = Column(DateTime, nullable=True)
    sla_policy_id = Column(UUID(as_uuid=True), ForeignKey("sla_policies.id", ondelete="SET NULL"), nullable=True)
    sla_breach = Column(Boolean, default=False)
    first_response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)  # cached AI summary JSON
    summary_cached_at = Column(DateTime, nullable=True)
    meta = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="conversations")
    contact = relationship("Contact", back_populates="conversations")
    assignee = relationship("User", back_populates="assigned_conversations", foreign_keys=[assigned_to])
    inbox = relationship("Inbox", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    sla_policy = relationship("SLAPolicy")
    ai_drafts = relationship("AIDraft", back_populates="conversation", cascade="all, delete-orphan")
