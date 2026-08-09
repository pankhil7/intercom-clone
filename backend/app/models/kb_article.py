import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, event
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from app.database import Base


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("kb_categories.id", ondelete="SET NULL"), nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # TipTap HTML
    content_text = Column(Text, nullable=True)  # stripped plain text for search
    status = Column(String(50), default="draft")  # draft | published | archived
    position = Column(Integer, default=0)
    views = Column(Integer, default=0)
    search_vector = Column(TSVECTOR, nullable=True)
    meta_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="kb_articles")
    category = relationship("KBCategory", back_populates="articles")
    author = relationship("User")
