from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_public: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_public: Optional[bool] = None


class CategoryResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    position: int
    is_public: bool
    article_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ArticleCreate(BaseModel):
    title: str
    content: str
    category_id: Optional[UUID] = None
    status: str = "draft"
    meta_description: Optional[str] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[UUID] = None
    status: Optional[str] = None
    meta_description: Optional[str] = None


class ArticleResponse(BaseModel):
    id: UUID
    organization_id: UUID
    category_id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    title: str
    slug: str
    content: str
    content_text: Optional[str] = None
    status: str
    views: int
    meta_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    status: str
    category: Optional[CategoryResponse] = None
    views: int
    created_at: datetime

    model_config = {"from_attributes": True}
