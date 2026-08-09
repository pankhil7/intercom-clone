import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class PageView(Base):
    __tablename__ = "contact_page_views"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    contact = relationship("Contact", back_populates="page_views")
