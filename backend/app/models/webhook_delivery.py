import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    attempt_count = Column(Integer, default=1)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    webhook = relationship("Webhook", back_populates="deliveries")
