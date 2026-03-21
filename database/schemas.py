"""
schemas.py
Pydantic Schemas — Request/Response models for the
Multi-Agent Research Assistant API

These match exactly the 5 DB tables:
  users | research_jobs | sources | agent_outputs | reports
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ──────────────────────────────────────────────
# USER SCHEMAS
# ──────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """User submits this to create an account."""
    email:    EmailStr
    username: str  = Field(..., min_length=3,  max_length=100)
    password: str  = Field(..., min_length=6,  max_length=128)


class UserLoginRequest(BaseModel):
    """User submits this to log in."""
    email:    EmailStr
    password: str


class UserResponse(BaseModel):
    """Returned to client — never expose password_hash."""
    id:            UUID
    email:         str
    username:      str
    is_active:     bool
    last_login_at: Optional[datetime]
    created_at:    datetime

    class Config:
        from_attributes = True   # allows building from SQLAlchemy model


class LoginResponse(BaseModel):
    """Returned after successful login."""
    message: str
    user:    UserResponse


# ──────────────────────────────────────────────
# RESEARCH JOB SCHEMAS
# ──────────────────────────────────────────────

class CreateJobRequest(BaseModel):
    """User submits this to start a new research job."""
    topic: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="The research topic — e.g. 'AI in healthcare 2025'"
    )
    depth: str = Field(
        default="detailed",
        description="How deep to research: 'quick' | 'detailed' | 'deep_dive'"
    )

    # Validate depth value
    from pydantic import field_validator
    @field_validator("depth")
    @classmethod
    def depth_must_be_valid(cls, v):
        allowed = {"quick", "detailed", "deep_dive"}
        if v not in allowed:
            raise ValueError(f"depth must be one of {allowed}")
        return v


class JobStatusResponse(BaseModel):
    """
    Returned when polling job status.
    UI polls this every few seconds while agents are running.
    """
    id:            UUID
    user_id:       UUID
    topic:         str
    depth:         str
    status:        str        # pending | running | completed | failed
    error_message: Optional[str]
    failed_agent:  Optional[str]
    started_at:    Optional[datetime]
    completed_at:  Optional[datetime]
    created_at:    datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Returned when user requests their list of past jobs."""
    jobs:  list[JobStatusResponse]
    total: int


class JobCreatedResponse(BaseModel):
    """Returned immediately after user submits a research topic."""
    job_id:  UUID
    topic:   str
    depth:   str
    status:  str     # always "pending" at this point
    message: str     # e.g. "Research started. Poll /jobs/{id} for status."


# ──────────────────────────────────────────────
# SOURCE SCHEMAS
# ──────────────────────────────────────────────

class SourceResponse(BaseModel):
    """
    A single web source found by the Researcher agent.
    Returned as part of the job detail or report.
    """
    id:                UUID
    job_id:            UUID
    url:               str
    title:             Optional[str]
    snippet:           Optional[str]
    agent_summary:     Optional[str]
    credibility_score: Optional[float]
    found_at:          datetime

    # full_content intentionally excluded — too large for API responses

    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    """All sources found for a specific research job."""
    job_id:  UUID
    sources: list[SourceResponse]
    total:   int


# ──────────────────────────────────────────────
# AGENT OUTPUT SCHEMAS
# ──────────────────────────────────────────────

class AgentOutputResponse(BaseModel):
    """
    Raw output from a single agent.
    Useful for debugging and showing progress in the UI.
    """
    id:               UUID
    job_id:           UUID
    agent_name:       str    # researcher | analyst | fact_checker | writer
    output_type:      str    # research | analysis | fact_check | draft_report
    content:          str
    llm_used:         Optional[str]
    tokens_used:      Optional[int]
    duration_seconds: Optional[float]
    created_at:       datetime

    class Config:
        from_attributes = True


class AgentOutputListResponse(BaseModel):
    """All agent outputs for a job — one per agent."""
    job_id:  UUID
    outputs: list[AgentOutputResponse]
    total:   int


class AgentProgressResponse(BaseModel):
    """
    Lightweight progress update shown in the UI while job is running.
    Tells the user which agent is currently working.
    """
    job_id:          UUID
    status:          str
    current_agent:   Optional[str]     # which agent is currently running
    agents_done:     list[str]         # agents that have finished
    agents_pending:  list[str]         # agents not yet started
    percent_complete: int              # 0, 25, 50, 75, 100


# ──────────────────────────────────────────────
# REPORT SCHEMAS
# ──────────────────────────────────────────────

class ReportResponse(BaseModel):
    """
    Full research report — the final output users care about.
    Includes the report content + metadata.
    """
    id:               UUID
    job_id:           UUID
    user_id:          UUID
    title:            str
    content_markdown: str
    file_path:        Optional[str]
    word_count:       Optional[int]
    source_count:     Optional[int]
    is_public:        bool
    created_at:       datetime

    class Config:
        from_attributes = True


class ReportSummaryResponse(BaseModel):
    """
    Lightweight report card — shown in the user's dashboard list.
    Does NOT include full content (too large for a list view).
    """
    id:           UUID
    job_id:       UUID
    title:        str
    word_count:   Optional[int]
    source_count: Optional[int]
    is_public:    bool
    created_at:   datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """All reports belonging to a user."""
    reports: list[ReportSummaryResponse]
    total:   int


class ReportWithSourcesResponse(BaseModel):
    """
    Full report + the sources used to write it.
    Shown on the report detail page.
    """
    report:  ReportResponse
    sources: list[SourceResponse]


# ──────────────────────────────────────────────
# JOB DETAIL SCHEMA (combined)
# ──────────────────────────────────────────────

class JobDetailResponse(BaseModel):
    """
    Full job detail — everything about a job in one response.
    Used on the job detail / report page.
    """
    job:     JobStatusResponse
    sources: list[SourceResponse]
    outputs: list[AgentOutputResponse]
    report:  Optional[ReportResponse]   # None if job not yet completed


# ──────────────────────────────────────────────
# HEALTH CHECK
# ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Returned by GET /health — check all services are up."""
    status:      str    # "healthy" | "degraded" | "down"
    database:    str    # "connected" | "disconnected"
    groq_status: str    # "reachable" | "unreachable"
    ollama_status: str  # "running" | "not running"
    mcp_server:  str    # "running" | "not running"
    version:     str    # app version string


# ──────────────────────────────────────────────
# ERROR SCHEMA
# ──────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response shape for all API errors."""
    error:   str           # short error code e.g. "job_not_found"
    message: str           # human readable message
    detail:  Optional[str] # extra debug info (only in development)