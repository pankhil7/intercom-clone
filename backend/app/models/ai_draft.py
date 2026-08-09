import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AIDraft(Base):
    __tablename__ = "ai_draft_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    draft_content = Column(Text, nullable=False)
    kb_articles_used = Column(ARRAY(UUID(as_uuid=True)), default=[])
    status = Column(String(50), default="pending")  # pending | accepted | dismissed | edited
    accepted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="ai_drafts")
    trigger_message = relationship("Message", foreign_keys=[message_id])
