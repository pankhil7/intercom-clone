import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CustomDomain(Base):
    __tablename__ = "custom_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    verification_token = Column(String(255), nullable=False)
    dns_record_type = Column(String(10), default="TXT")
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    ssl_status = Column(String(50), default="pending")  # pending | provisioning | active | failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="custom_domains")
