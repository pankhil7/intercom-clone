import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(String(50), default="free")
    widget_color = Column(String(7), default="#6366f1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    inboxes = relationship("Inbox", back_populates="organization", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="organization", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="organization", cascade="all, delete-orphan")
    kb_categories = relationship("KBCategory", back_populates="organization", cascade="all, delete-orphan")
    kb_articles = relationship("KBArticle", back_populates="organization", cascade="all, delete-orphan")
    canned_responses = relationship("CannedResponse", back_populates="organization", cascade="all, delete-orphan")
    sla_policies = relationship("SLAPolicy", back_populates="organization", cascade="all, delete-orphan")
    custom_domains = relationship("CustomDomain", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
