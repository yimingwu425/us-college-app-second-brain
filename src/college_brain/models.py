from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SCHEMA_VERSION = 5


class TaskStatus(StrEnum):
    NOT_STARTED = "未开始"
    IN_PROGRESS = "进行中"
    WAITING_STUDENT = "待学生"
    BLOCKED = "阻塞"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


TERMINAL_TASK_STATUSES = {TaskStatus.COMPLETED, TaskStatus.CANCELLED}


class DatePrecision(StrEnum):
    EXACT = "exact"
    DATE_ONLY = "date_only"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class ArtifactStatus(StrEnum):
    OUTLINE = "提纲"
    DRAFT = "草稿"
    REVIEW = "待审核"
    FINAL = "最终版"
    SUBMITTED = "已提交"
    ARCHIVED = "已归档"


class VaultConfig(BaseModel):
    schema_version: Literal[5] = SCHEMA_VERSION
    student_timezone: str = "Asia/Shanghai"
    timezone_confirmed: bool = False
    application_cycle_start: str | None = None
    knowledge_path: str = "knowledge"

    @field_validator("application_cycle_start")
    @classmethod
    def validate_cycle(cls, value: str | None) -> str | None:
        if value is not None:
            datetime.strptime(value, "%Y-%m")
        return value


class RecordMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal[5] = SCHEMA_VERSION
    id: str
    type: str
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    source_refs: list[str] = Field(default_factory=list)
    confidence: str = "confirmed"
    supersedes: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class TaskMeta(RecordMeta):
    type: Literal["task"] = "task"
    title: str
    status: TaskStatus = TaskStatus.NOT_STARTED
    task_type: str = "general"
    deadline: datetime | None = None
    deadline_precision: DatePrecision = DatePrecision.UNKNOWN
    timezone: str | None = None
    deadline_source: str | None = None
    deadline_checked_at: datetime | None = None
    school_id: str | None = None
    application_round: str | None = None
    next_action: str | None = None
    completion_evidence: str | None = None
    reopen_reason: str | None = None

    @field_validator("deadline", "deadline_checked_at")
    @classmethod
    def require_aware_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("deadline 时间必须包含时区")
        return value

    @field_validator("completion_evidence", "reopen_reason")
    @classmethod
    def normalize_evidence(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class CheckpointMeta(RecordMeta):
    type: Literal["checkpoint"] = "checkpoint"
    current_goal: str = ""
    active_task_ids: list[str] = Field(default_factory=list)
    just_completed: list[str] = Field(default_factory=list)
    next_action: str = ""
    waiting_or_blocked: str = ""
    resume_files: list[str] = Field(default_factory=list)


class KnowledgeSourceMeta(RecordMeta):
    type: Literal["advisor_transcript"] = "advisor_transcript"
    title: str
    advisor: str = "unknown"
    platform: str | None = None
    source_url: str | None = None
    published_at: str | None = None
    imported_at: datetime
    applicable_cycles: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    copyright_status: str = "undetermined"
    import_key: str


class SchoolApplicationMeta(RecordMeta):
    type: Literal["school_application"] = "school_application"
    school_id: str
    school_name: str
    status: str = "考虑中"
    application_round: str | None = None
    intended_major: str | None = None
    requirements_checked_at: datetime | None = None
    requirement_source: str | None = None
    missing_items: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    final_artifact_ids: list[str] = Field(default_factory=list)
    student_confirmed: bool = False
    submitted_at: datetime | None = None
    submission_evidence: str | None = None


class ArtifactMeta(RecordMeta):
    type: Literal["application_artifact"] = "application_artifact"
    artifact_id: str
    artifact_type: str
    version: int = 1
    status: ArtifactStatus = ArtifactStatus.DRAFT
    target_school_id: str | None = None
    prompt: str | None = None
    limit: int | None = None
    limit_unit: str | None = None
    source_material_ids: list[str] = Field(default_factory=list)
    student_confirmed: bool = False
    supersedes_version: int | None = None


class ValidationIssue(BaseModel):
    level: Literal["error", "warning"]
    path: Path
    message: str


def dumpable(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json", exclude_none=True)
