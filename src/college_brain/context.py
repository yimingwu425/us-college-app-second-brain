from __future__ import annotations

import re
from pathlib import Path

from .checkpoint import load_checkpoint
from .markdown import MarkdownFormatError, read_markdown
from .tasks import list_tasks, task_timing
from .vault import load_config, local_now


BASE_CONTEXT_FILES = [
    "学生档案/核心信息.md",
    "学生档案/约束与偏好.md",
    "用户画像.md",
]


def _query_terms(query: str) -> set[str]:
    ascii_words = re.findall(r"[A-Za-z0-9_-]{2,}", query.lower())
    chinese = re.findall(r"[\u4e00-\u9fff]{2,}", query)
    pairs = [word[index : index + 2] for word in chinese for index in range(len(word) - 1)]
    return set(ascii_words + chinese + pairs)


def related_files(root: Path, query: str, limit: int = 5) -> list[str]:
    terms = _query_terms(query)
    if not terms:
        return []
    candidates: list[tuple[int, str]] = []
    excluded = {"申请追踪/总览.md", "状态/当前.md", "迁移报告.md"}
    for path in root.rglob("*.md"):
        relative = path.relative_to(root).as_posix()
        if relative in excluded or relative.startswith("会话/") or relative.startswith("knowledge/"):
            continue
        try:
            metadata, body = read_markdown(path)
        except MarkdownFormatError:
            metadata, body = {}, path.read_text(encoding="utf-8")
        if metadata.get("status") == "superseded":
            continue
        text = body.lower()
        score = sum(text.count(term) for term in terms)
        if score:
            candidates.append((score, relative))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [relative for _, relative in candidates[:limit]]


def _excerpt(body: str, query: str, max_chars: int = 2000) -> str:
    text = body.strip()
    if len(text) <= max_chars or not query:
        return text[:max_chars]
    terms = _query_terms(query)
    lowered = text.lower()
    positions = [lowered.find(term.lower()) for term in terms if lowered.find(term.lower()) >= 0]
    if not positions:
        return text[:max_chars]
    center = min(positions)
    start = max(0, center - max_chars // 3)
    end = min(len(text), start + max_chars)
    if end - start < max_chars:
        start = max(0, end - max_chars)
    prefix = "…" if start else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def build_context(root: Path, query: str = "") -> dict:
    now = local_now(root)
    config = load_config(root)
    months_to_cycle = None
    if config.application_cycle_start:
        cycle_year, cycle_month = map(int, config.application_cycle_start.split("-"))
        months_to_cycle = (cycle_year - now.year) * 12 + cycle_month - now.month
    checkpoint = load_checkpoint(root)
    tasks = []
    for task in list_tasks(root):
        tasks.append(
            {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "timing": task_timing(task, now),
                "next_action": task.next_action,
            }
        )

    query_matches = related_files(root, query)
    paths = list(dict.fromkeys([*BASE_CONTEXT_FILES, *checkpoint.resume_files, *query_matches]))
    excerpts = []
    for relative in paths:
        path = root / relative
        if not path.is_file():
            continue
        try:
            _, body = read_markdown(path)
        except MarkdownFormatError:
            body = path.read_text(encoding="utf-8")
        if relative in checkpoint.resume_files:
            reason = "checkpoint"
        elif relative in query_matches:
            reason = "query_match"
        else:
            reason = "base_context"
        excerpts.append({"path": relative, "reason": reason, "content": _excerpt(body, query if reason == "query_match" else "")})

    return {
        "now": now.isoformat(timespec="seconds"),
        "timezone": config.student_timezone,
        "timezone_confirmed": config.timezone_confirmed,
        "application_cycle_start": config.application_cycle_start,
        "months_to_application_cycle": months_to_cycle,
        "checkpoint": checkpoint.model_dump(mode="json", exclude_none=True),
        "open_tasks": tasks,
        "records": excerpts,
    }


def render_context(context: dict) -> str:
    lines = [
        f"当前时间：{context['now']}",
        f"学生时区：{context['timezone']}（{'已确认' if context['timezone_confirmed'] else '待学生确认'}）",
    ]
    if context.get("months_to_application_cycle") is not None:
        lines.append(f"距申请季开始：约 {context['months_to_application_cycle']} 个月（按当前年月动态计算）")
    checkpoint = context["checkpoint"]
    if checkpoint.get("current_goal"):
        lines.append(f"当前目标：{checkpoint['current_goal']}")
    if checkpoint.get("next_action"):
        lines.append(f"下一步：{checkpoint['next_action']}")
    if context["open_tasks"]:
        lines.append("\n开放任务：")
        for task in context["open_tasks"]:
            timing = f"，{task['timing']}" if task["timing"] else ""
            lines.append(f"- [{task['status']}] {task['id']} {task['title']}{timing}")
    if context["records"]:
        lines.append("\n相关记录：")
        for record in context["records"]:
            lines.append(f"\n### {record['path']}（{record['reason']}）\n{record['content']}")
    return "\n".join(lines)
