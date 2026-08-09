import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.kb_article import KBArticle
from app.models.kb_category import KBCategory
from app.models.user import User
from app.schemas.kb import (
    ArticleCreate,
    ArticleListItem,
    ArticleResponse,
    ArticleUpdate,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)

from app.logging_config import get_logger

router = APIRouter(prefix="/kb", tags=["knowledge-base"])
logger = get_logger(__name__)


def _strip_html(html: str) -> str:
    """Strip HTML tags to get plain text."""
    clean = re.compile(r"<[^>]+>")
    return re.sub(clean, "", html)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text


def _unique_slug(base_slug: str, db: Session, model, org_id: UUID, exclude_id: Optional[UUID] = None) -> str:
    slug = base_slug
    counter = 1
    while True:
        q = db.query(model).filter(model.organization_id == org_id, model.slug == slug)
        if exclude_id:
            q = q.filter(model.id != exclude_id)
        if not q.first():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(KBCategory).filter(KBCategory.organization_id == current_user.organization_id)
    categories = q.order_by(KBCategory.position, KBCategory.created_at).all()

    result = []
    for cat in categories:
        article_count = (
            db.query(func.count(KBArticle.id))
            .filter(KBArticle.category_id == cat.id)
            .scalar()
            or 0
        )
        result.append(
            CategoryResponse(
                id=cat.id,
                organization_id=cat.organization_id,
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                icon=cat.icon,
                position=cat.position,
                is_public=cat.is_public,
                article_count=article_count,
                created_at=cat.created_at,
            )
        )
    return result


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_slug = payload.slug or _slugify(payload.name)
    slug = _unique_slug(base_slug, db, KBCategory, current_user.organization_id)

    cat = KBCategory(
        organization_id=current_user.organization_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        icon=payload.icon,
        is_public=payload.is_public,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)

    return CategoryResponse(
        id=cat.id,
        organization_id=cat.organization_id,
        name=cat.name,
        slug=cat.slug,
        description=cat.description,
        icon=cat.icon,
        position=cat.position,
        is_public=cat.is_public,
        article_count=0,
        created_at=cat.created_at,
    )


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(KBCategory).filter(
        KBCategory.id == category_id,
        KBCategory.organization_id == current_user.organization_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if payload.name is not None:
        cat.name = payload.name
    if payload.slug is not None:
        cat.slug = _unique_slug(payload.slug, db, KBCategory, current_user.organization_id, exclude_id=category_id)
    if payload.description is not None:
        cat.description = payload.description
    if payload.icon is not None:
        cat.icon = payload.icon
    if payload.is_public is not None:
        cat.is_public = payload.is_public

    db.commit()
    db.refresh(cat)

    article_count = (
        db.query(func.count(KBArticle.id))
        .filter(KBArticle.category_id == cat.id)
        .scalar()
        or 0
    )

    return CategoryResponse(
        id=cat.id,
        organization_id=cat.organization_id,
        name=cat.name,
        slug=cat.slug,
        description=cat.description,
        icon=cat.icon,
        position=cat.position,
        is_public=cat.is_public,
        article_count=article_count,
        created_at=cat.created_at,
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(KBCategory).filter(
        KBCategory.id == category_id,
        KBCategory.organization_id == current_user.organization_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    db.delete(cat)
    db.commit()


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

@router.get("/articles", response_model=List[ArticleListItem])
def list_articles(
    category_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(KBArticle).filter(KBArticle.organization_id == current_user.organization_id)

    if category_id:
        q = q.filter(KBArticle.category_id == category_id)
    if status_filter:
        q = q.filter(KBArticle.status == status_filter)

    offset = (page - 1) * limit
    articles = q.order_by(KBArticle.created_at.desc()).offset(offset).limit(limit).all()

    result = []
    for article in articles:
        cat_response = None
        if article.category:
            article_count = (
                db.query(func.count(KBArticle.id))
                .filter(KBArticle.category_id == article.category.id)
                .scalar()
                or 0
            )
            cat_response = CategoryResponse(
                id=article.category.id,
                organization_id=article.category.organization_id,
                name=article.category.name,
                slug=article.category.slug,
                description=article.category.description,
                icon=article.category.icon,
                position=article.category.position,
                is_public=article.category.is_public,
                article_count=article_count,
                created_at=article.category.created_at,
            )
        result.append(
            ArticleListItem(
                id=article.id,
                title=article.title,
                slug=article.slug,
                status=article.status,
                category=cat_response,
                views=article.views,
                created_at=article.created_at,
            )
        )
    return result


@router.post("/articles", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_slug = _slugify(payload.title)
    slug = _unique_slug(base_slug, db, KBArticle, current_user.organization_id)
    content_text = _strip_html(payload.content)

    article = KBArticle(
        organization_id=current_user.organization_id,
        category_id=payload.category_id,
        author_id=current_user.id,
        title=payload.title,
        slug=slug,
        content=payload.content,
        content_text=content_text,
        status=payload.status,
        meta_description=payload.meta_description,
    )
    db.add(article)
    db.flush()

    # Update search_vector using PostgreSQL tsvector
    db.execute(
        text(
            "UPDATE kb_articles SET search_vector = to_tsvector('english', :title || ' ' || coalesce(:content, '')) WHERE id = :id"
        ),
        {"title": payload.title, "content": content_text, "id": str(article.id)},
    )

    db.commit()
    db.refresh(article)
    logger.info("kb_article_created", article_id=str(article.id), status=article.status, org_id=str(current_user.organization_id))
    return article


@router.get("/articles/slug/{slug}", response_model=ArticleResponse)
def get_article_by_slug(
    slug: str,
    org: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(KBArticle).filter(KBArticle.slug == slug, KBArticle.status == "published")
    if org:
        from app.models.organization import Organization
        organization = db.query(Organization).filter(Organization.slug == org).first()
        if organization:
            q = q.filter(KBArticle.organization_id == organization.id)

    article = q.first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    # Increment view count
    article.views = (article.views or 0) + 1
    db.commit()
    db.refresh(article)
    return article


@router.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    article = db.query(KBArticle).filter(
        KBArticle.id == article_id,
        KBArticle.organization_id == current_user.organization_id,
    ).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


@router.patch("/articles/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: UUID,
    payload: ArticleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    article = db.query(KBArticle).filter(
        KBArticle.id == article_id,
        KBArticle.organization_id == current_user.organization_id,
    ).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    if payload.title is not None:
        article.title = payload.title
    if payload.content is not None:
        article.content = payload.content
        article.content_text = _strip_html(payload.content)
    if payload.category_id is not None:
        article.category_id = payload.category_id
    if payload.status is not None:
        article.status = payload.status
    if payload.meta_description is not None:
        article.meta_description = payload.meta_description

    db.flush()

    # Recompute search_vector
    db.execute(
        text(
            "UPDATE kb_articles SET search_vector = to_tsvector('english', :title || ' ' || coalesce(:content, '')) WHERE id = :id"
        ),
        {
            "title": article.title,
            "content": article.content_text or "",
            "id": str(article.id),
        },
    )

    db.commit()
    db.refresh(article)
    if payload.status is not None:
        logger.info("kb_article_status_changed", article_id=str(article.id), status=article.status, org_id=str(current_user.organization_id))
    return article


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    article = db.query(KBArticle).filter(
        KBArticle.id == article_id,
        KBArticle.organization_id == current_user.organization_id,
    ).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    db.delete(article)
    db.commit()


@router.get("/search")
def search_articles(
    q: str = Query(..., min_length=1),
    org: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(KBArticle).filter(KBArticle.status == "published")

    if org:
        from app.models.organization import Organization
        organization = db.query(Organization).filter(Organization.slug == org).first()
        if organization:
            query = query.filter(KBArticle.organization_id == organization.id)

    articles = (
        query.filter(
            KBArticle.search_vector.op("@@")(func.to_tsquery("english", q))
        )
        .order_by(
            func.ts_rank(KBArticle.search_vector, func.to_tsquery("english", q)).desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(a.id),
            "title": a.title,
            "slug": a.slug,
            "excerpt": (a.content_text or "")[:200],
        }
        for a in articles
    ]
