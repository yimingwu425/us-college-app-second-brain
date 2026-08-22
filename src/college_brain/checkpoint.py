from __future__ import annotations

from pathlib import Path

from .markdown import read_markdown, write_markdown
from .models import CheckpointMeta, RecordMeta, TERMINAL_TASK_STATUSES, TaskMeta, dumpable
from .vault import utc_now


CHECKPOINT_PATH = Path("状态/当前.md")


def load_checkpoint(root: Path) -> CheckpointMeta:
    metadata, _ = read_markdown(root / CHECKPOINT_PATH)
    return CheckpointMeta.model_validate(metadata)


def update_checkpoint(
    root: Path,
    *,
    current_goal: str | None,
    active_task_ids: list[str] | None,
    just_completed: list[str] | None,
    next_action: str | None,
    waiting_or_blocked: str | None,
    resume_files: list[str] | None,
) -> Path:
    checkpoint_path = root / CHECKPOINT_PATH
    current = load_checkpoint(root)
    changes = current.model_dump()
    if active_task_ids is not None:
        task_dir = root / "申请追踪/任务"
        valid_active: list[str] = []
        for task_id in active_task_ids:
            task_file = task_dir / f"{task_id}.md"
            if not task_file.is_file():
                continue
            metadata, _ = read_markdown(task_file)
            task = TaskMeta.model_validate(metadata)
            if task.status not in TERMINAL_TASK_STATUSES:
                valid_active.append(task_id)
        active_task_ids = valid_active
    for key, value in {
        "current_goal": current_goal,
        "active_task_ids": active_task_ids,
        "just_completed": just_completed,
        "next_action": next_action,
        "waiting_or_blocked": waiting_or_blocked,
        "resume_files": resume_files,
    }.items():
        if value is not None:
            changes[key] = value
    changes["updated_at"] = utc_now()
    updated = CheckpointMeta.model_validate(changes)
    body = "# 当前状态\n\n这个文件由 `brain checkpoint update` 覆盖维护。\n"
    write_markdown(checkpoint_path, dumpable(updated), body)

    session_id = updated.updated_at.strftime("%Y%m%dT%H%M%S%fZ")
    session_path = root / "会话" / updated.updated_at.strftime("%Y-%m") / f"{session_id}.md"
    session_meta = RecordMeta(
        id=f"session-{session_id}",
        type="session_handoff",
        status="complete",
        created_at=updated.updated_at,
        updated_at=updated.updated_at,
        source_refs=[CHECKPOINT_PATH.as_posix()],
        links=updated.resume_files,
    )
    session_body = (
        f"# 会话交接 {updated.updated_at.isoformat(timespec='seconds')}\n\n"
        f"- 当前目标：{updated.current_goal}\n"
        f"- 活跃任务：{', '.join(updated.active_task_ids)}\n"
        f"- 刚完成：{', '.join(updated.just_completed)}\n"
        f"- 下一步：{updated.next_action}\n"
        f"- 等待/阻塞：{updated.waiting_or_blocked}\n"
        f"- 恢复文件：{', '.join(updated.resume_files)}\n"
    )
    write_markdown(session_path, dumpable(session_meta), session_body)
    return checkpoint_path
