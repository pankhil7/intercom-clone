import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import jsonschema
from sqlalchemy.orm import Session
from sqlalchemy import text
from groq import Groq
from app.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.kb_article import KBArticle
from app.models.ai_draft import AIDraft
from app.utils.sanitizer import (
    sanitize_dict_strings,
    sanitize_string,
    apply_profanity_filter,
    extract_urls,
    strip_unverified_urls,
)

logger = logging.getLogger(__name__)

SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["problem", "sentiment", "key_points", "suggested_action"],
    "properties": {
        "problem": {"type": "string", "maxLength": 300},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "frustrated"]},
        "key_points": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "suggested_action": {"type": "string", "maxLength": 300},
    },
}

DRAFT_SCHEMA = {
    "type": "object",
    "required": ["draft", "kb_article_ids_used"],
    "properties": {
        "draft": {"type": "string", "maxLength": 600},
        "kb_article_ids_used": {"type": "array", "items": {"type": "string"}},
    },
}


def get_groq_client():
    if not settings.GROQ_API_KEY:
        return None
    return Groq(api_key=settings.GROQ_API_KEY)


def build_conversation_text(messages: list) -> str:
    from app.utils.sanitizer import strip_html

    lines = []
    for msg in messages:
        sender = "Customer" if msg.sender_type == 'contact' else "Agent"
        ts = msg.created_at.strftime("%Y-%m-%d %H:%M") if msg.created_at else ""
        content = strip_html(msg.content)[:500]
        lines.append(f"[{ts}] {sender}: {content}")
    return "\n".join(lines)


def search_kb_articles(db: Session, org_id, query: str, limit: int = 3) -> list:
    try:
        results = db.execute(
            text("""
                SELECT id, title, content_text, slug,
                       ts_rank(search_vector, plainto_tsquery('english', :query)) AS rank
                FROM kb_articles
                WHERE organization_id = :org_id
                  AND status = 'published'
                  AND search_vector @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {"org_id": str(org_id), "query": query, "limit": limit},
        ).fetchall()
        return results
    except Exception:
        # Fallback: ILIKE search
        results = db.execute(
            text("""
                SELECT id, title, content_text, slug
                FROM kb_articles
                WHERE organization_id = :org_id
                  AND status = 'published'
                  AND (title ILIKE :q OR content_text ILIKE :q)
                LIMIT :limit
            """),
            {"org_id": str(org_id), "q": f"%{query}%", "limit": limit},
        ).fetchall()
        return results


async def summarize_conversation(db: Session, conversation_id) -> tuple:
    """Returns (summary_dict, is_cached)."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        return None, False

    # Check cache
    if conversation.summary and conversation.summary_cached_at:
        cache_age = datetime.utcnow() - conversation.summary_cached_at
        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .first()
        )

        if (
            cache_age < timedelta(minutes=10)
            and last_msg
            and last_msg.created_at
            and last_msg.created_at <= conversation.summary_cached_at
        ):
            try:
                return json.loads(conversation.summary), True
            except Exception:
                pass

    client = get_groq_client()
    if not client:
        return {
            "problem": "AI service not configured",
            "sentiment": "neutral",
            "key_points": [],
            "suggested_action": "Please configure GROQ_API_KEY",
        }, False

    # Build context: first message + last 20
    first_msg = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .first()
    )

    recent_msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(20)
        .all()
    )
    recent_msgs = list(reversed(recent_msgs))

    all_msgs = [first_msg] if first_msg else []
    for m in recent_msgs:
        if not all_msgs or m.id != all_msgs[0].id:
            all_msgs.append(m)

    total_count = db.query(Message).filter(Message.conversation_id == conversation_id).count()
    conv_text = build_conversation_text(all_msgs)

    prompt = f"""You are a customer support assistant. Analyze this conversation and return ONLY valid JSON.
Use ONLY information present in the conversation. Do not add any information not explicitly stated.
If a field's information is not in the conversation, use "Not mentioned".

Conversation ({total_count} total messages, showing key messages):
{conv_text}

Return JSON matching this exact structure:
{{
  "problem": "One sentence describing what the customer's issue is",
  "sentiment": "positive|neutral|negative|frustrated",
  "key_points": ["point 1", "point 2"],
  "suggested_action": "One sentence on what the agent should do next"
}}

Do not include any text before or after the JSON."""

    fallback = {
        "problem": "Unable to generate summary",
        "sentiment": "neutral",
        "key_points": [],
        "suggested_action": "Please review the conversation manually",
    }

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            jsonschema.validate(data, SUMMARY_SCHEMA)

            # Sanitize
            data = sanitize_dict_strings(data)

            # Length caps
            data["problem"] = (data.get("problem") or "Not mentioned")[:300]
            data["suggested_action"] = (data.get("suggested_action") or "Not mentioned")[:300]
            data["key_points"] = [
                (p[:200] if p else "") for p in (data.get("key_points") or [])[:5]
            ]

            # Fill empty
            for field in ["problem", "suggested_action"]:
                if not data.get(field):
                    data[field] = "Not mentioned"

            # Cache in DB
            conversation.summary = json.dumps(data)
            conversation.summary_cached_at = datetime.utcnow()
            db.commit()

            return data, False

        except (json.JSONDecodeError, jsonschema.ValidationError) as e:
            logger.warning(f"Summary validation failed attempt {attempt + 1}: {e}")
            if attempt == 2:
                return fallback, False
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return fallback, False

    return fallback, False


async def generate_draft(
    db: Session, conversation_id, trigger_message_id=None
) -> Optional[AIDraft]:
    """Generate an AI reply draft using RAG with KB articles."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        return None

    client = get_groq_client()
    if not client:
        return None

    # Get trigger message (latest contact message)
    if trigger_message_id:
        trigger_msg = db.query(Message).filter(Message.id == trigger_message_id).first()
    else:
        trigger_msg = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.sender_type == 'contact',
            )
            .order_by(Message.created_at.desc())
            .first()
        )

    if not trigger_msg:
        return None

    # RAG: find relevant KB articles
    query_text = sanitize_string(trigger_msg.content)[:500]
    kb_rows = search_kb_articles(db, conversation.organization_id, query_text, limit=3)

    kb_context = ""
    kb_ids = []
    if kb_rows:
        for i, row in enumerate(kb_rows):
            article_text = (row.content_text or "")[:800]
            kb_context += f"\n[Article {i + 1}: {row.title} (ID: {row.id})]\n{article_text}\n"
            kb_ids.append(str(row.id))

    # Build conversation context
    first_msg = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .first()
    )

    recent_msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    recent_msgs = list(reversed(recent_msgs))

    all_msgs = [first_msg] if first_msg else []
    for m in recent_msgs:
        if not all_msgs or m.id != all_msgs[0].id:
            all_msgs.append(m)

    conv_text = build_conversation_text(all_msgs)

    kb_instruction = (
        f"""
Knowledge Base Articles (your ONLY source of factual information):
{kb_context if kb_context else "No relevant articles found."}
"""
        if kb_context
        else "No knowledge base articles are available. If you cannot answer from the conversation context alone, say you will look into it."
    )

    prompt = f"""You are a helpful customer support agent. Draft a reply to the customer's latest message.

IMPORTANT RULES:
- Use ONLY information from the Knowledge Base articles provided
- Do NOT invent facts, procedures, or URLs not in the articles
- If the articles don't address the question, say "I'll look into this for you and get back to you shortly"
- Keep your reply concise and professional (under 400 characters)
- Return ONLY valid JSON, no other text
{kb_instruction}

Conversation:
{conv_text}

Return JSON:
{{"draft": "<reply text here>", "kb_article_ids_used": ["<article_id_1>"]}}"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            jsonschema.validate(data, DRAFT_SCHEMA)

            draft_text = sanitize_string(data.get("draft", ""))[:500]

            # Profanity filter
            filtered = apply_profanity_filter(draft_text)
            if filtered is None:
                logger.warning("AI draft contained profanity, suppressed")
                return None
            draft_text = filtered

            # Strip unverified URLs
            if kb_rows:
                allowed_urls = []
                for row in kb_rows:
                    if row.content_text:
                        allowed_urls.extend(extract_urls(row.content_text))
                draft_text = strip_unverified_urls(draft_text, allowed_urls)

            if not draft_text:
                return None

            # Validate KB article IDs exist
            valid_ids = []
            for aid in data.get("kb_article_ids_used", []):
                try:
                    article = db.query(KBArticle).filter(
                        KBArticle.id == aid,
                        KBArticle.organization_id == conversation.organization_id,
                    ).first()
                    if article:
                        valid_ids.append(UUID(aid))
                except Exception:
                    pass

            draft = AIDraft(
                conversation_id=conversation_id,
                message_id=trigger_message_id,
                draft_content=draft_text,
                kb_articles_used=valid_ids,
                status='pending',
            )
            db.add(draft)
            db.commit()
            db.refresh(draft)

            # Notify agent via WebSocket
            try:
                from app.socket.server import sio

                asyncio.create_task(
                    sio.emit(
                        'ai:draft_ready',
                        {
                            'conversation_id': str(conversation_id),
                            'draft_id': str(draft.id),
                            'content_preview': draft_text[:100],
                        },
                        room=f'org:{conversation.organization_id}',
                    )
                )
            except Exception:
                pass

            return draft

        except Exception as e:
            logger.error(f"Draft generation attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                return None
            await asyncio.sleep(0.5)

    return None
