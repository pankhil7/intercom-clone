from typing import List
from pydantic import BaseModel
from uuid import UUID


class OverviewResponse(BaseModel):
    total_conversations: int
    open_conversations: int
    resolved_conversations: int
    avg_first_response_mins: float
    avg_resolution_mins: float
    sla_breach_rate: float


class AgentPerf(BaseModel):
    id: UUID
    name: str
    conversations_handled: int
    avg_response_mins: float
    resolved_count: int


class AgentPerfResponse(BaseModel):
    agents: List[AgentPerf]


class BusiestHoursResponse(BaseModel):
    heatmap: List[List[int]]  # [day][hour] - 7 days x 24 hours


class ResolutionPoint(BaseModel):
    date: str
    opened: int
    resolved: int
    rate: float


class ResolutionRateResponse(BaseModel):
    series: List[ResolutionPoint]
