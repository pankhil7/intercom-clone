from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class SummaryResponse(BaseModel):
    problem: str
    sentiment: str
    key_points: List[str]
    suggested_action: str
    cached: bool
    generated_at: Optional[datetime] = None


class DraftResponse(BaseModel):
    id: UUID
    content: str
    kb_articles_used: List[UUID] = []
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DraftUpdate(BaseModel):
    status: str
    edited_content: Optional[str] = None


class KBSuggestItem(BaseModel):
    id: UUID
    title: str
    excerpt: str
    slug: str


class KBSuggestResponse(BaseModel):
    articles: List[KBSuggestItem]
