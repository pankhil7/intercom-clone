from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.ai_draft import AIDraft
from app.models.conversation import Conversation
from app.models.kb_article import KBArticle
from app.models.user import User
from app.schemas.ai import DraftResponse, DraftUpdate, KBSuggestItem, KBSuggestResponse, SummaryResponse
from app.services.ai_service import generate_draft, summarize_conversation

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/summarize/{conversation_id}", response_model=SummaryResponse)
def summarize(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    result = summarize_conversation(conversation=conv, db=db)
    return result


@router.post("/draft/{conversation_id}", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
def draft(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == current_user.organization_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    ai_draft = generate_draft(conversation=conv, db=db)

    return DraftResponse(
        id=ai_draft.id,
        content=ai_draft.draft_content,
        kb_articles_used=ai_draft.kb_articles_used or [],
        status=ai_draft.status,
        created_at=ai_draft.created_at,
    )


@router.patch("/draft/{draft_id}", response_model=DraftResponse)
def update_draft(
    draft_id: UUID,
    payload: DraftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ensure the draft belongs to a conversation in the current user's org
    ai_draft = (
        db.query(AIDraft)
        .join(Conversation, AIDraft.conversation_id == Conversation.id)
        .filter(
            AIDraft.id == draft_id,
            Conversation.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not ai_draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    ai_draft.status = payload.status
    if payload.edited_content is not None:
        ai_draft.draft_content = payload.edited_content

    db.commit()
    db.refresh(ai_draft)

    return DraftResponse(
        id=ai_draft.id,
        content=ai_draft.draft_content,
        kb_articles_used=ai_draft.kb_articles_used or [],
        status=ai_draft.status,
        created_at=ai_draft.created_at,
    )


@router.get("/kb-suggest", response_model=KBSuggestResponse)
def kb_suggest(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    articles = (
        db.query(KBArticle)
        .filter(
            KBArticle.organization_id == current_user.organization_id,
            KBArticle.status == "published",
            KBArticle.search_vector.op("@@")(func.to_tsquery("english", q)),
        )
        .order_by(
            func.ts_rank(KBArticle.search_vector, func.to_tsquery("english", q)).desc()
        )
        .limit(3)
        .all()
    )

    items = [
        KBSuggestItem(
            id=a.id,
            title=a.title,
            excerpt=(a.content_text or "")[:200],
            slug=a.slug,
        )
        for a in articles
    ]

    return KBSuggestResponse(articles=items)
