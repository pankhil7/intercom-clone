from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.analytics import (
    AgentPerf,
    AgentPerfResponse,
    BusiestHoursResponse,
    OverviewResponse,
    ResolutionPoint,
    ResolutionRateResponse,
)

from app.logging_config import get_logger

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = get_logger(__name__)


def _parse_dt(value: Optional[str], default: datetime) -> datetime:
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return default
    return default


@router.get("/overview", response_model=OverviewResponse)
def overview(
    start: Optional[str] = None,
    end: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import timedelta

    now = datetime.utcnow()
    start_dt = _parse_dt(start, now - timedelta(days=30))
    end_dt = _parse_dt(end, now)

    base_q = db.query(Conversation).filter(
        Conversation.organization_id == current_user.organization_id,
        Conversation.created_at >= start_dt,
        Conversation.created_at <= end_dt,
    )

    total = base_q.count()
    open_count = base_q.filter(Conversation.status == "open").count()
    resolved_count = base_q.filter(Conversation.status == "resolved").count()

    # Average first response time in minutes
    first_response_rows = (
        db.query(
            func.avg(
                func.extract("epoch", Conversation.first_response_at - Conversation.created_at) / 60
            )
        )
        .filter(
            Conversation.organization_id == current_user.organization_id,
            Conversation.created_at >= start_dt,
            Conversation.created_at <= end_dt,
            Conversation.first_response_at != None,
        )
        .scalar()
    )
    avg_first_response = float(first_response_rows or 0)

    # Average resolution time in minutes
    resolution_rows = (
        db.query(
            func.avg(
                func.extract("epoch", Conversation.resolved_at - Conversation.created_at) / 60
            )
        )
        .filter(
            Conversation.organization_id == current_user.organization_id,
            Conversation.created_at >= start_dt,
            Conversation.created_at <= end_dt,
            Conversation.resolved_at != None,
        )
        .scalar()
    )
    avg_resolution = float(resolution_rows or 0)

    # SLA breach rate
    breach_count = base_q.filter(Conversation.sla_breach == True).count()
    sla_breach_rate = (breach_count / total) if total > 0 else 0.0

    return OverviewResponse(
        total_conversations=total,
        open_conversations=open_count,
        resolved_conversations=resolved_count,
        avg_first_response_mins=round(avg_first_response, 2),
        avg_resolution_mins=round(avg_resolution, 2),
        sla_breach_rate=round(sla_breach_rate, 4),
    )


@router.get("/agent-performance", response_model=AgentPerfResponse)
def agent_performance(
    start: Optional[str] = None,
    end: Optional[str] = None,
    agent_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import timedelta

    now = datetime.utcnow()
    start_dt = _parse_dt(start, now - timedelta(days=30))
    end_dt = _parse_dt(end, now)

    agents_q = db.query(User).filter(
        User.organization_id == current_user.organization_id,
        User.is_active == True,
    )
    if agent_id:
        agents_q = agents_q.filter(User.id == agent_id)

    agents = agents_q.all()
    result = []

    for agent in agents:
        conversations_handled = (
            db.query(func.count(Conversation.id))
            .filter(
                Conversation.organization_id == current_user.organization_id,
                Conversation.assigned_to == agent.id,
                Conversation.created_at >= start_dt,
                Conversation.created_at <= end_dt,
            )
            .scalar()
            or 0
        )

        resolved_count = (
            db.query(func.count(Conversation.id))
            .filter(
                Conversation.organization_id == current_user.organization_id,
                Conversation.assigned_to == agent.id,
                Conversation.status == "resolved",
                Conversation.created_at >= start_dt,
                Conversation.created_at <= end_dt,
            )
            .scalar()
            or 0
        )

        avg_response = (
            db.query(
                func.avg(
                    func.extract("epoch", Conversation.first_response_at - Conversation.created_at) / 60
                )
            )
            .filter(
                Conversation.organization_id == current_user.organization_id,
                Conversation.assigned_to == agent.id,
                Conversation.created_at >= start_dt,
                Conversation.created_at <= end_dt,
                Conversation.first_response_at != None,
            )
            .scalar()
        )

        result.append(
            AgentPerf(
                id=agent.id,
                name=agent.full_name,
                conversations_handled=conversations_handled,
                avg_response_mins=round(float(avg_response or 0), 2),
                resolved_count=resolved_count,
            )
        )

    return AgentPerfResponse(agents=result)


@router.get("/busiest-hours", response_model=BusiestHoursResponse)
def busiest_hours(
    start: Optional[str] = None,
    end: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import timedelta

    now = datetime.utcnow()
    start_dt = _parse_dt(start, now - timedelta(days=30))
    end_dt = _parse_dt(end, now)

    # Initialize 7x24 matrix (0=Mon ... 6=Sun)
    heatmap = [[0] * 24 for _ in range(7)]

    rows = (
        db.query(
            # PostgreSQL dow: 0=Sun, 1=Mon ... 6=Sat; we want 0=Mon
            extract("dow", Conversation.created_at).label("dow"),
            extract("hour", Conversation.created_at).label("hour"),
            func.count(Conversation.id).label("cnt"),
        )
        .filter(
            Conversation.organization_id == current_user.organization_id,
            Conversation.created_at >= start_dt,
            Conversation.created_at <= end_dt,
        )
        .group_by("dow", "hour")
        .all()
    )

    for row in rows:
        # Convert Sunday=0 (postgres) to Monday=0 convention
        pg_dow = int(row.dow)  # 0=Sun
        day_idx = (pg_dow - 1) % 7   # Sun(0)->6, Mon(1)->0, ...
        hour_idx = int(row.hour)
        heatmap[day_idx][hour_idx] = int(row.cnt)

    return BusiestHoursResponse(heatmap=heatmap)


@router.get("/resolution-rate", response_model=ResolutionRateResponse)
def resolution_rate(
    start: Optional[str] = None,
    end: Optional[str] = None,
    group_by: str = Query("day", regex="^(day|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import timedelta

    now = datetime.utcnow()
    start_dt = _parse_dt(start, now - timedelta(days=30))
    end_dt = _parse_dt(end, now)

    # Choose date truncation
    trunc_map = {"day": "day", "week": "week", "month": "month"}
    trunc = trunc_map.get(group_by, "day")

    opened_rows = (
        db.query(
            func.date_trunc(trunc, Conversation.created_at).label("period"),
            func.count(Conversation.id).label("cnt"),
        )
        .filter(
            Conversation.organization_id == current_user.organization_id,
            Conversation.created_at >= start_dt,
            Conversation.created_at <= end_dt,
        )
        .group_by("period")
        .order_by("period")
        .all()
    )

    resolved_rows = (
        db.query(
            func.date_trunc(trunc, Conversation.resolved_at).label("period"),
            func.count(Conversation.id).label("cnt"),
        )
        .filter(
            Conversation.organization_id == current_user.organization_id,
            Conversation.resolved_at >= start_dt,
            Conversation.resolved_at <= end_dt,
        )
        .group_by("period")
        .order_by("period")
        .all()
    )

    opened_map = {row.period: int(row.cnt) for row in opened_rows}
    resolved_map = {row.period: int(row.cnt) for row in resolved_rows}

    all_periods = sorted(set(list(opened_map.keys()) + list(resolved_map.keys())))

    series = []
    for period in all_periods:
        opened = opened_map.get(period, 0)
        resolved = resolved_map.get(period, 0)
        rate = (resolved / opened) if opened > 0 else 0.0
        series.append(
            ResolutionPoint(
                date=period.strftime("%Y-%m-%d") if hasattr(period, "strftime") else str(period),
                opened=opened,
                resolved=resolved,
                rate=round(rate, 4),
            )
        )

    return ResolutionRateResponse(series=series)
