import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True)
    visitor_id = Column(String(255), nullable=True, index=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    timezone = Column(String(100), nullable=True)
    location = Column(JSONB, default={})
    custom_attributes = Column(JSONB, default={})
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="contacts")
    conversations = relationship("Conversation", back_populates="contact")
    page_views = relationship("PageView", back_populates="contact", cascade="all, delete-orphan")
