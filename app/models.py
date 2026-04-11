from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, field_validator


class TaskStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    complete = "complete"
    failed = "failed"
    cancelled = "cancelled"


# ── Request Models ─────────────────────────────────────────────────────────────

class SendReportRequest(BaseModel):
    report_type: Literal["sales", "inventory", "users", "analytics"]
    recipient_email: EmailStr
    date_from: str
    date_to: str
    include_charts: bool = False

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class ProcessDataRequest(BaseModel):
    data: list[dict]
    operation: Literal["clean", "transform", "analyze", "export"]
    output_format: Literal["json", "csv", "summary"] = "json"

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v: list) -> list:
        if len(v) < 1:
            raise ValueError("data must contain at least 1 item")
        if len(v) > 1000:
            raise ValueError("data must contain at most 1000 items")
        return v


class SyncIntegrationRequest(BaseModel):
    source: Literal["stripe", "github", "shopify", "airtable"]
    sync_type: Literal["full", "delta"]
    since_date: Optional[str] = None


# ── Response Models ────────────────────────────────────────────────────────────

class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: TaskStatus
    owner_id: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_seconds: int
    progress: int
    result: Optional[dict] = None
    error: Optional[str] = None
    params: dict


class TaskStats(BaseModel):
    total_tasks: int
    by_status: dict
    by_type: dict
    success_rate: float
    avg_completion_seconds: float
    recent_tasks: list