from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from .markdown import read_markdown, write_markdown
from .models import (
    DatePrecision,
    TERMINAL_TASK_STATUSES,
    TaskMeta,
    TaskStatus,
    dumpable,
)
from .vault import load_config, local_now, utc_now


def task_path(root: Path, task_id: str) -> Path:
    return root / "申请追踪/任务" / f"{task_id}.md"


def parse_deadline(value: str | None, timezone: str) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone))
    return parsed


def validate_deadline_precision(value: str | None, precision: DatePrecision) -> None:
    if value is None and precision != DatePrecision.UNKNOWN:
        raise ValueError("没有 deadline 时 precision 必须是 unknown")
    if value is not None and precision == DatePrecision.UNKNOWN:
        raise ValueError("有 deadline 时必须声明 exact、date_only 或 estimated")
    if value and precision == DatePrecision.EXACT and "T" not in value and " " not in value:
        raise ValueError("exact deadline 必须包含具体时刻；只有日期请使用 date_only")


def add_task(
    root: Path,
    *,
    task_id: str,
    title: str,
    deadline: str | None,
    precision: DatePrecision,
    task_type: str,
    next_action: str | None,
    source_refs: list[str],
    school_id: str | None,
    application_round: str | None,
    deadline_timezone: str | None = None,
    deadline_source: str | None = None,
    deadline_checked_at: str | None = None,
) -> Path:
    path = task_path(root, task_id)
    if path.exists():
        raise ValueError(f"Task already exists: {task_id}")
    config = load_config(root)
    task_timezone = deadline_timezone or config.student_timezone
    validate_deadline_precision(deadline, precision)
    now = utc_now()
    meta = TaskMeta(
        id=task_id,
        title=title,
        created_at=now,
        updated_at=now,
        deadline=parse_deadline(deadline, task_timezone),
        deadline_precision=precision,
        timezone=task_timezone,
        deadline_source=deadline_source,
        deadline_checked_at=parse_deadline(deadline_checked_at, config.student_timezone),
        task_type=task_type,
        next_action=next_action,
        source_refs=source_refs,
        school_id=school_id,
        application_round=application_round,
    )
    write_markdown(path, dumpable(meta), f"# {title}\n")
    return path


def load_task(path: Path) -> tuple[TaskMeta, str]:
    metadata, body = read_markdown(path)
    return TaskMeta.model_validate(metadata), body


def update_task(
    root: Path,
    task_id: str,
    *,
    status: TaskStatus | None,
    next_action: str | None,
    completion_evidence: str | None,
    deadline: str | None,
    precision: DatePrecision | None,
    deadline_timezone: str | None = None,
    deadline_source: str | None = None,
    deadline_checked_at: str | None = None,
    reopen_reason: str | None = None,
) -> Path:
    path = task_path(root, task_id)
    meta, body = load_task(path)
    changes = meta.model_dump()
    if status is not None:
        if meta.status in TERMINAL_TASK_STATUSES and status not in TERMINAL_TASK_STATUSES:
            if not reopen_reason:
                raise ValueError("Reopening a completed/cancelled task requires --reopen-reason")
            changes["reopen_reason"] = reopen_reason
        changes["status"] = status
    if next_action is not None:
        changes["next_action"] = next_action
    if completion_evidence is not None:
        changes["completion_evidence"] = completion_evidence
    if deadline is not None:
        effective_precision = precision or meta.deadline_precision
        validate_deadline_precision(deadline, effective_precision)
        timezone = deadline_timezone or meta.timezone or load_config(root).student_timezone
        changes["deadline"] = parse_deadline(deadline, timezone)
    if deadline_timezone is not None:
        if deadline is None and meta.deadline is not None:
            raise ValueError("修改 deadline 时区必须同时提供 --deadline，避免误解释原截止时间")
        changes["timezone"] = deadline_timezone
    if deadline_source is not None:
        changes["deadline_source"] = deadline_source
    if deadline_checked_at is not None:
        changes["deadline_checked_at"] = parse_deadline(deadline_checked_at, load_config(root).student_timezone)
    if precision is not None:
        deadline_value = deadline
        if deadline_value is None and meta.deadline is not None:
            deadline_value = meta.deadline.isoformat()
        validate_deadline_precision(deadline_value, precision)
        changes["deadline_precision"] = precision
    if changes["status"] == TaskStatus.COMPLETED and not changes.get("completion_evidence"):
        raise ValueError("Completing a task requires --completion-evidence")
    if changes["status"] in TERMINAL_TASK_STATUSES:
        changes["next_action"] = None
    changes["updated_at"] = utc_now()
    updated = TaskMeta.model_validate(changes)
    write_markdown(path, dumpable(updated), body)
    return path


def list_tasks(root: Path, *, include_terminal: bool = False) -> list[TaskMeta]:
    result: list[TaskMeta] = []
    for path in sorted((root / "申请追踪/任务").glob("*.md")):
        task, _ = load_task(path)
        if include_terminal or task.status not in TERMINAL_TASK_STATUSES:
            result.append(task)
    return sorted(
        result,
        key=lambda item: (
            item.deadline is None,
            item.deadline or datetime.max.replace(tzinfo=ZoneInfo("UTC")),
        ),
    )


def task_timing(task: TaskMeta, now: datetime) -> str:
    if task.status in TERMINAL_TASK_STATUSES or task.deadline is None:
        return ""
    if task.deadline_precision in {DatePrecision.DATE_ONLY, DatePrecision.ESTIMATED}:
        local_deadline = datetime.combine(task.deadline.date(), time.max, tzinfo=task.deadline.tzinfo).astimezone(now.tzinfo)
    else:
        local_deadline = task.deadline.astimezone(now.tzinfo)
    seconds = (local_deadline - now).total_seconds()
    if seconds < 0:
        return "逾期"
    if seconds <= 30 * 86400:
        return "30天内"
    return ""


def refresh_overview(root: Path) -> Path:
    path = root / "申请追踪/总览.md"
    metadata, _ = read_markdown(path)
    now = local_now(root)
    rows = []
    for task in list_tasks(root, include_terminal=True):
        deadline = task.deadline.astimezone(now.tzinfo).isoformat(timespec="minutes") if task.deadline else ""
        rows.append(
            f"| {task.id} | {task.title} | {deadline} | {task.deadline_precision.value} | "
            f"{task.status.value} | {task_timing(task, now)} | {task.next_action or ''} |"
        )
    body = "# 申请任务总览\n\n"
    body += f"> 生成于 {now.isoformat(timespec='seconds')}。请勿手改，任务文件是唯一状态源。\n\n"
    body += "| ID | 事项 | 截止 | 精度 | 状态 | 动态提醒 | 下一步 |\n"
    body += "| --- | --- | --- | --- | --- | --- | --- |\n"
    body += "\n".join(rows)
    metadata["updated_at"] = utc_now().isoformat()
    write_markdown(path, metadata, body)
    return path
