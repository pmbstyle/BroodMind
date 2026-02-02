from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkerRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    status: str
    task: str
    granted_caps: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    # Worker results (populated when completed)
    summary: str | None = None
    output: dict[str, Any] | None = None
    error: str | None = None


class IntentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    worker_id: str
    type: str
    payload: dict[str, Any]
    payload_hash: str
    risk: str
    requires_approval: bool
    status: str
    created_at: datetime


class WorkerTemplateRecord(BaseModel):
    """Worker template - pre-defined agent with system prompt."""
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    description: str
    system_prompt: str  # Worker's personality and purpose
    available_tools: list[str]  # Tool names this worker can use
    required_permissions: list[str]  # ["network", "fs_read", "fs_write", "exec"]
    max_thinking_steps: int = 10
    default_timeout_seconds: int = 300
    created_at: datetime
    updated_at: datetime


class PermitRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    intent_id: str
    intent_type: str
    worker_id: str
    payload_hash: str
    expires_at: datetime
    consumed_at: datetime | None = None
    created_at: datetime


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    ts: datetime
    correlation_id: str | None = None
    level: Literal["debug", "info", "warning", "error", "critical"]
    event_type: str
    data: dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    role: str
    content: str
    embedding: list[float] | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
