from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError

from .checkpoint import load_checkpoint
from .markdown import MarkdownFormatError, read_markdown
from .models import ArtifactMeta, RecordMeta, SCHEMA_VERSION, SchoolApplicationMeta, TERMINAL_TASK_STATUSES, TaskMeta, ValidationIssue
from .schools import submission_readiness
from .vault import load_config, load_manifest


def validate_vault(root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = load_manifest()
    config_path = root / "vault.yaml"
    if not config_path.is_file():
        return [ValidationIssue(level="error", path=config_path, message="缺少 vault.yaml")]
    try:
        config = load_config(root)
        ZoneInfo(config.student_timezone)
    except (ValidationError, ZoneInfoNotFoundError, ValueError) as exc:
        issues.append(ValidationIssue(level="error", path=config_path, message=str(exc)))

    for relative in manifest["directories"]:
        path = root / relative
        if not path.is_dir():
            issues.append(ValidationIssue(level="error", path=path, message="缺少必需目录"))
    for relative in manifest["files"]:
        path = root / relative
        if not path.is_file():
            issues.append(ValidationIssue(level="error", path=path, message="缺少必需文件"))

    open_tasks: dict[str, TaskMeta] = {}
    school_records: list[tuple[Path, SchoolApplicationMeta]] = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root).as_posix()
        if relative in {"AGENTS.md", "CLAUDE.md", "README.md"}:
            continue
        if "knowledge" in path.parts and "sources" not in path.parts:
            continue
        try:
            metadata, _ = read_markdown(path)
            if metadata.get("type") == "task":
                task = TaskMeta.model_validate(metadata)
                if task.status not in TERMINAL_TASK_STATUSES:
                    open_tasks[task.id] = task
            elif metadata.get("type") == "school_application":
                school_records.append((path, SchoolApplicationMeta.model_validate(metadata)))
            elif metadata.get("type") == "application_artifact":
                ArtifactMeta.model_validate(metadata)
            else:
                RecordMeta.model_validate(metadata)
            if metadata.get("schema_version") != SCHEMA_VERSION:
                raise ValueError("schema_version 不是 5")
        except (MarkdownFormatError, ValidationError, ValueError) as exc:
            issues.append(ValidationIssue(level="error", path=path, message=str(exc)))

    for path, school in school_records:
        try:
            ready, _ = submission_readiness(root, school)
        except (MarkdownFormatError, ValidationError, ValueError) as exc:
            issues.append(ValidationIssue(level="error", path=path, message=f"提交条件无法检查：{exc}"))
            continue
        if ready and school.status not in {"已提交", "已取消"}:
            related_open = [task_id for task_id, task in open_tasks.items() if task.school_id == school.school_id]
            if related_open:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        path=path,
                        message=f"学校已满足提交条件，但仍有开放任务：{', '.join(related_open)}",
                    )
                )

    try:
        checkpoint = load_checkpoint(root)
        for relative in checkpoint.resume_files:
            if not (root / relative).exists():
                issues.append(
                    ValidationIssue(level="warning", path=root / relative, message="checkpoint 引用了不存在的文件")
                )
    except (MarkdownFormatError, ValidationError) as exc:
        issues.append(ValidationIssue(level="error", path=root / "状态/当前.md", message=str(exc)))
    return issues
