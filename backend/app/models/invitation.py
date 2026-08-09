import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="agent")
    token = Column(String(255), unique=True, nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])
