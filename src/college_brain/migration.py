from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .markdown import read_markdown, write_markdown
from .models import ArtifactMeta, ArtifactStatus, DatePrecision, RecordMeta, SchoolApplicationMeta, TaskStatus, dumpable
from .tasks import add_task
from .vault import init_vault, utc_now


@dataclass
class MigrationReport:
    source: Path
    target: Path
    copied: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    mappings: list[tuple[str, str]] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            "# v4 到 v5 迁移报告",
            "",
            f"- 来源：`{self.source.name}`",
            f"- 目标：`{self.target.name}`",
            f"- 生成时间：{utc_now().isoformat(timespec='seconds')}",
            "",
            "## 路径映射",
            "",
        ]
        lines.extend(f"- `{source}` -> `{target}`" for source, target in self.mappings)
        lines.extend(["", "## 警告", ""])
        if self.warnings:
            lines.extend(f"- {warning}" for warning in self.warnings)
        else:
            lines.append("- 无")
        return "\n".join(lines) + "\n"


def slug(value: str, fallback: str = "record") -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value.strip().lower()).strip("-")
    return value[:60] or fallback


def iter_old_markdown(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.md"):
        if ".git" not in path.parts and "dist" not in path.parts:
            yield path


def _write_record(root: Path, relative: str, record_id: str, record_type: str, title: str, body: str, source: str) -> None:
    now = utc_now()
    metadata = RecordMeta(
        id=record_id,
        type=record_type,
        created_at=now,
        updated_at=now,
        source_refs=[source],
    )
    write_markdown(root / relative, dumpable(metadata), f"# {title}\n\n{body.strip()}\n")


def _migrate_profile(old_root: Path, new_root: Path, report: MigrationReport) -> None:
    mapping = {
        "本体画像/00-核心身份.md": "学生档案/核心信息.md",
        "本体画像/01-价值观与原则.md": "学生档案/约束与偏好.md",
        "本体画像/02-背景与经历.md": "学生档案/学业与课程.md",
        "本体画像/03-兴趣与热爱.md": "学生档案/约束与偏好.md",
    }
    for old_relative, new_relative in mapping.items():
        source = old_root / old_relative
        if not source.exists():
            report.warnings.append(f"缺少旧档案：{old_relative}")
            continue
        _, body = _legacy_body(source)
        target = new_root / new_relative
        _, current = read_markdown(target)
        write_markdown(
            target,
            {**read_markdown(target)[0], "source_refs": list(dict.fromkeys([*read_markdown(target)[0].get("source_refs", []), old_relative])), "updated_at": utc_now().isoformat()},
            f"{current.rstrip()}\n\n## 迁移自 `{old_relative}`\n\n{body.strip()}\n",
        )
        report.mappings.append((old_relative, new_relative))

    profile = old_root / "用户画像.md"
    if profile.exists():
        _, body = _legacy_body(profile)
        target = new_root / "用户画像.md"
        metadata, _ = read_markdown(target)
        write_markdown(target, {**metadata, "source_refs": ["用户画像.md"], "updated_at": utc_now().isoformat()}, f"# 用户画像\n\n迁移自旧版本；这里保留理解、主题和故事假设，不作为学生事实唯一来源。\n\n{body.strip()}\n")
        report.mappings.append(("用户画像.md", "用户画像.md"))


def _legacy_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        return read_markdown(path)
    return {}, text


def _unique_relative(base: Path, kind: str, title: str, source: Path, used: set[str]) -> tuple[Path, str]:
    stem = slug(title)
    record_id = stem
    relative = Path("素材库") / kind / f"{stem}.md"
    suffix = 2
    while relative.as_posix() in used or (base / relative).exists():
        record_id = f"{stem}-{suffix}"
        relative = Path("素材库") / kind / f"{record_id}.md"
        suffix += 1
    used.add(relative.as_posix())
    return relative, record_id


def _migrate_materials(old_root: Path, new_root: Path, report: MigrationReport) -> None:
    base = old_root / "素材库"
    if not base.exists():
        return
    used: set[str] = set()
    for source in sorted(base.rglob("*.md")):
        relative = source.relative_to(base)
        kind = relative.parts[0] if relative.parts else "经历"
        title = source.stem
        target_relative, record_id = _unique_relative(new_root, kind, title, source, used)
        _, body = _legacy_body(source)
        _write_record(new_root, target_relative.as_posix(), record_id, f"material_{kind}", title, body, source.relative_to(old_root).as_posix())
        report.mappings.append((source.relative_to(old_root).as_posix(), target_relative.as_posix()))


def _legacy_school_fields(body: str) -> dict[str, object]:
    fields: dict[str, object] = {}
    match = re.search(r"^\s*-\s*轮次：\s*(.+?)\s*$", body, re.MULTILINE)
    if match and match.group(1) not in {"未定", "未知", "—", "-"}:
        fields["application_round"] = match.group(1).strip()
    match = re.search(r"^\s*-\s*材料缺口：\s*(.+?)\s*$", body, re.MULTILINE)
    if match:
        fields["missing_items"] = [item.strip() for item in re.split(r"[、,，;；]", match.group(1)) if item.strip()]
    match = re.search(r"^\s*-\s*下一步：\s*(.+?)\s*$", body, re.MULTILINE)
    if match:
        fields["next_actions"] = [match.group(1).strip()]
    return fields


def _migrate_schools(old_root: Path, new_root: Path, report: MigrationReport) -> None:
    base = old_root / "学校研究"
    if base.exists():
        for source in sorted(base.glob("*.md")):
            school_id = slug(source.stem, "school")
            _, body = _legacy_body(source)
            target = Path("学校研究") / school_id / "事实.md"
            _write_record(new_root, target.as_posix(), f"school-{school_id}", "school_research", source.stem, body, source.relative_to(old_root).as_posix())
            report.mappings.append((source.relative_to(old_root).as_posix(), target.as_posix()))

    progress = old_root / "申请追踪/每所学校进度"
    if not progress.exists():
        return
    for source in sorted(progress.glob("*.md")):
        school_id = slug(source.stem, "school")
        _, body = _legacy_body(source)
        fields = _legacy_school_fields(body)
        target = Path("申请追踪/学校") / f"{school_id}.md"
        existing = new_root / target
        if existing.exists():
            metadata, current = read_markdown(existing)
            for key, value in fields.items():
                if value:
                    if key == "application_round" and not metadata.get(key):
                        metadata[key] = value
                    elif key in {"missing_items", "next_actions"}:
                        metadata[key] = list(dict.fromkeys([*metadata.get(key, []), *value]))
            metadata["source_refs"] = list(dict.fromkeys([*metadata.get("source_refs", []), source.relative_to(old_root).as_posix()]))
            metadata["updated_at"] = utc_now().isoformat()
            write_markdown(existing, metadata, f"{current.rstrip()}\n\n## 迁移自 `{source.relative_to(old_root).as_posix()}`\n\n{body.strip()}\n")
        else:
            now = utc_now()
            metadata = SchoolApplicationMeta(
                id=f"school-application-{school_id}",
                school_id=school_id,
                school_name=source.stem,
                created_at=now,
                updated_at=now,
                source_refs=[source.relative_to(old_root).as_posix()],
                **fields,
            )
            write_markdown(existing, dumpable(metadata), f"# {source.stem} 申请状态\n\n{body.strip()}\n")
        report.mappings.append((source.relative_to(old_root).as_posix(), target.as_posix()))


def _status(value: str) -> TaskStatus:
    value = value.strip()
    if any(word in value for word in ("取消", "作废")):
        return TaskStatus.CANCELLED
    if any(word in value for word in ("未提交", "未完成", "待做", "未开始", "规划")):
        return TaskStatus.NOT_STARTED
    if any(word in value for word in ("已完成", "已交", "已提交")):
        return TaskStatus.COMPLETED
    if any(word in value for word in ("进行", "开始")):
        return TaskStatus.IN_PROGRESS
    if any(word in value for word in ("阻塞", "等待")):
        return TaskStatus.BLOCKED
    return TaskStatus.NOT_STARTED


def _migrate_deadlines(old_root: Path, new_root: Path, report: MigrationReport) -> None:
    source = old_root / "申请追踪/Deadline总览.md"
    if not source.exists():
        return
    text = source.read_text(encoding="utf-8")
    for index, line in enumerate(text.splitlines(), start=1):
        if not line.startswith("|") or "---" in line or "事项" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        title, date_value, school, status = cells[:4]
        task_id = f"legacy-{slug(title, f'task-{index}')}-{index}"
        precision = DatePrecision.DATE_ONLY if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value) else DatePrecision.UNKNOWN
        deadline = date_value if precision == DatePrecision.DATE_ONLY else None
        if precision == DatePrecision.UNKNOWN and date_value:
            report.warnings.append(f"Deadline 第 {index} 行日期精度无法确认：{date_value}（保留为空，需人工核验）")
        initial_status = _status(status)
        try:
            path = add_task(
                new_root,
                task_id=task_id,
                title=title,
                deadline=deadline,
                precision=precision,
                task_type="legacy_deadline",
                next_action=None if initial_status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED} else None,
                source_refs=["申请追踪/Deadline总览.md"],
                school_id=slug(school) if school else None,
                application_round=None,
            )
            if initial_status == TaskStatus.COMPLETED:
                report.warnings.append(f"未自动把旧状态标为已完成：{title}（需要完成依据）")
            elif initial_status in {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED}:
                metadata, body = read_markdown(path)
                metadata["status"] = initial_status.value
                metadata["updated_at"] = utc_now().isoformat()
                write_markdown(path, metadata, body)
            report.mappings.append((f"申请追踪/Deadline总览.md:{index}", path.relative_to(new_root).as_posix()))
        except ValueError as exc:
            report.warnings.append(f"Deadline 第 {index} 行未迁移：{exc}")


def _migrate_artifacts(old_root: Path, new_root: Path, report: MigrationReport) -> None:
    type_by_folder = {"文书": "essay", "活动列表": "activity", "推荐信": "recommendation"}
    for top, artifact_type in type_by_folder.items():
        base = old_root / top
        if not base.exists():
            continue
        for source in sorted(base.rglob("*.md")):
            relative = source.relative_to(old_root)
            target_relative = Path("申请材料") / relative
            _, body = _legacy_body(source)
            now = utc_now()
            artifact_id = slug(source.stem)
            version_match = re.search(r"(?:^|[-_])v(\d+)", source.stem, re.IGNORECASE)
            version = int(version_match.group(1)) if version_match else 1
            status = ArtifactStatus.OUTLINE if "outline" in source.stem.lower() else ArtifactStatus.DRAFT
            metadata = ArtifactMeta(
                id=f"artifact-{artifact_id}-v{version}",
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                version=version,
                status=status,
                created_at=now,
                updated_at=now,
                source_refs=[relative.as_posix()],
            )
            write_markdown(new_root / target_relative, dumpable(metadata), f"# {source.stem}\n\n{body.strip()}\n")
            report.mappings.append((relative.as_posix(), target_relative.as_posix()))


def migrate_v4(source: Path, target: Path, *, dry_run: bool = False, timezone: str = "Asia/Shanghai", cycle: str | None = None) -> MigrationReport:
    source = source.resolve()
    target = target.resolve()
    if not source.is_dir():
        raise ValueError(f"旧 vault 不存在：{source}")
    if target.exists() and any(target.iterdir()):
        raise ValueError(f"迁移目标不为空：{target}")
    report = MigrationReport(source=source, target=target)
    if dry_run:
        with tempfile.TemporaryDirectory(prefix="college-brain-migration-") as temporary:
            preview_target = Path(temporary) / "vault"
            preview = migrate_v4(source, preview_target, dry_run=False, timezone=timezone, cycle=cycle)
            report.mappings = preview.mappings
            report.warnings = [*preview.warnings, "dry-run：未写入目标目录"]
        return report
    init_vault(target, timezone=timezone, cycle=cycle)
    _migrate_profile(source, target, report)
    _migrate_materials(source, target, report)
    _migrate_schools(source, target, report)
    _migrate_deadlines(source, target, report)
    _migrate_artifacts(source, target, report)
    conversation = source / "对话历史.md"
    if conversation.exists():
        _, body = _legacy_body(conversation)
        target_path = target / "会话/迁移-旧对话历史.md"
        _write_record(target, target_path.relative_to(target).as_posix(), "legacy-conversation", "session_handoff", "旧对话历史", body, "对话历史.md")
        report.mappings.append(("对话历史.md", target_path.relative_to(target).as_posix()))
    report_path = target / "迁移报告.md"
    report_meta = RecordMeta(
        id="migration-report",
        type="migration_report",
        status="complete",
        created_at=utc_now(),
        updated_at=utc_now(),
        source_refs=[source.as_posix()],
    )
    write_markdown(report_path, dumpable(report_meta), report.render())
    return report
