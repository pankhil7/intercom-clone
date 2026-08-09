import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = Column(String(50), nullable=False)  # contact | agent | bot | system
    sender_id = Column(UUID(as_uuid=True), nullable=True)  # user.id for agents
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # text | html | activity
    attachments = Column(JSONB, default=[])
    email_message_id = Column(String(500), nullable=True, index=True)
    email_in_reply_to = Column(String(500), nullable=True)
    email_references = Column(ARRAY(String), nullable=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    meta = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
