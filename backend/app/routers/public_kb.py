"""Public Knowledge Base endpoints — no authentication required."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.kb_article import KBArticle
from app.models.kb_category import KBCategory
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/public/kb", tags=["public-kb"])


def _get_org(slug: str, db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


def _article_dict(a: KBArticle, include_content: bool = False) -> dict:
    excerpt = ""
    if a.content:
        # Strip basic HTML tags for excerpt
        import re
        plain = re.sub(r'<[^>]+>', '', a.content)
        excerpt = plain[:200].strip()

    d = {
        "id": str(a.id),
        "title": a.title,
        "slug": a.slug,
        "excerpt": excerpt,
        "view_count": a.view_count,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }
    if a.author_id:
        d["author"] = {
            "id": str(a.author_id),
            "full_name": a.author.full_name if a.author else None,
        }
    if include_content:
        d["content"] = a.content
        if a.category:
            d["category"] = {"id": str(a.category.id), "name": a.category.name}
    return d


@router.get("/{org_slug}/categories")
def list_public_categories(org_slug: str, db: Session = Depends(get_db)):
    org = _get_org(org_slug, db)

    categories = (
        db.query(KBCategory)
        .filter(KBCategory.organization_id == org.id)
        .order_by(KBCategory.position)
        .all()
    )

    result = []
    for cat in categories:
        articles = (
            db.query(KBArticle)
            .filter(
                KBArticle.category_id == cat.id,
                KBArticle.status == "published",
            )
            .order_by(KBArticle.updated_at.desc())
            .limit(10)
            .all()
        )
        result.append({
            "id": str(cat.id),
            "name": cat.name,
            "description": cat.description,
            "icon": cat.icon,
            "articles": [_article_dict(a) for a in articles],
        })

    return {"categories": result}


@router.get("/{org_slug}/search")
def search_public_articles(
    org_slug: str,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    org = _get_org(org_slug, db)

    # PostgreSQL full-text search
    try:
        articles = (
            db.query(KBArticle)
            .filter(
                KBArticle.organization_id == org.id,
                KBArticle.status == "published",
                KBArticle.search_vector.op("@@")(func.plainto_tsquery("english", q)),
            )
            .order_by(
                func.ts_rank(
                    KBArticle.search_vector,
                    func.plainto_tsquery("english", q),
                ).desc()
            )
            .limit(limit)
            .all()
        )
    except Exception:
        # Fallback: ILIKE search
        articles = (
            db.query(KBArticle)
            .filter(
                KBArticle.organization_id == org.id,
                KBArticle.status == "published",
                KBArticle.title.ilike(f"%{q}%"),
            )
            .limit(limit)
            .all()
        )

    return {"articles": [_article_dict(a) for a in articles]}


@router.get("/{org_slug}/articles/{slug}")
def get_public_article(org_slug: str, slug: str, db: Session = Depends(get_db)):
    org = _get_org(org_slug, db)

    article = (
        db.query(KBArticle)
        .filter(
            KBArticle.organization_id == org.id,
            KBArticle.slug == slug,
            KBArticle.status == "published",
        )
        .first()
    )
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    # Increment view count
    article.view_count = (article.view_count or 0) + 1
    db.commit()

    return {"article": _article_dict(article, include_content=True)}
