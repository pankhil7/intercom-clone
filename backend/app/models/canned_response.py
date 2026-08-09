import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CannedResponse(Base):
    __tablename__ = "canned_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    shortcut = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="canned_responses")
    creator = relationship("User", foreign_keys=[created_by])
