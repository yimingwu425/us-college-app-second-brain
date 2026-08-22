from __future__ import annotations

from datetime import datetime
from importlib.resources import files
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from .markdown import atomic_write, read_markdown, write_markdown
from .models import CheckpointMeta, RecordMeta, VaultConfig, dumpable


FIXED_RECORDS = {
    "学生档案/核心信息.md": ("profile-core", "student_profile", "核心信息"),
    "学生档案/学业与课程.md": ("profile-academic", "student_profile", "学业与课程"),
    "学生档案/标化考试.md": ("profile-tests", "student_profile", "标化考试"),
    "学生档案/荣誉.md": ("profile-honors", "student_profile", "荣誉"),
    "学生档案/约束与偏好.md": ("profile-preferences", "student_profile", "约束与偏好"),
    "用户画像.md": ("profile-insights", "profile_insights", "用户画像"),
}


def utc_now() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))


def load_manifest() -> dict:
    resource = files("college_brain").joinpath("data/vault_manifest.yaml")
    return yaml.safe_load(resource.read_text(encoding="utf-8"))


def init_vault(root: Path, *, timezone: str, cycle: str | None) -> list[Path]:
    root = root.resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"Target directory is not empty: {root}")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {timezone}") from exc

    root.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    created: list[Path] = []
    for directory in manifest["directories"]:
        path = root / directory
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
        placeholder = path / ".gitkeep"
        placeholder.touch(exist_ok=True)
        created.append(placeholder)

    config = VaultConfig(student_timezone=timezone, application_cycle_start=cycle)
    config_path = root / "vault.yaml"
    atomic_write(
        config_path,
        yaml.safe_dump(config.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
    )
    created.append(config_path)

    now = utc_now()
    for relative, (record_id, record_type, title) in FIXED_RECORDS.items():
        meta = RecordMeta(
            id=record_id,
            type=record_type,
            created_at=now,
            updated_at=now,
        )
        body = f"# {title}\n\n"
        if relative == "用户画像.md":
            body += "这里只记录带来源的长期理解、主题与故事假设，不复制学生事实。\n"
        else:
            body += "学生事实的权威记录。可直接修改；重要变更由本地工具记录更新时间。\n"
        path = root / relative
        write_markdown(path, dumpable(meta), body)
        created.append(path)

    checkpoint = CheckpointMeta(
        id="current-checkpoint",
        created_at=now,
        updated_at=now,
    )
    checkpoint_path = root / "状态/当前.md"
    write_markdown(checkpoint_path, dumpable(checkpoint), "# 当前状态\n")
    created.append(checkpoint_path)

    overview = root / "申请追踪/总览.md"
    overview_meta = RecordMeta(
        id="task-overview",
        type="generated_view",
        status="generated",
        created_at=now,
        updated_at=now,
    )
    write_markdown(
        overview,
        dumpable(overview_meta),
        "# 申请任务总览\n\n由 `brain task list` 生成；任务文件是唯一状态源。\n",
    )
    created.append(overview)

    catalog = root / "knowledge/catalog.yaml"
    atomic_write(catalog, "schema_version: 5\nsources: []\n")
    created.append(catalog)

    gitignore = root / ".gitignore"
    atomic_write(
        gitignore,
        ".brain/\nknowledge/inbox/*\n!knowledge/inbox/.gitkeep\nknowledge/sources/*\n!knowledge/sources/.gitkeep\n",
    )
    created.append(gitignore)
    return created


def find_vault(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "vault.yaml").is_file():
            return candidate
    raise FileNotFoundError(f"No vault.yaml found from {start}")


def load_config(root: Path) -> VaultConfig:
    raw = yaml.safe_load((root / "vault.yaml").read_text(encoding="utf-8")) or {}
    return VaultConfig.model_validate(raw)


def local_now(root: Path) -> datetime:
    config = load_config(root)
    return datetime.now(tz=ZoneInfo(config.student_timezone))


def supersede_records(root: Path, record_ids: list[str]) -> list[Path]:
    pending = set(record_ids)
    matches: list[tuple[Path, dict, str]] = []
    for path in root.rglob("*.md"):
        if "knowledge" in path.parts:
            continue
        try:
            metadata, body = read_markdown(path)
        except ValueError:
            continue
        if metadata.get("id") in pending:
            matches.append((path, metadata, body))
            pending.remove(metadata["id"])
    if pending:
        raise ValueError(f"找不到要替代的记录：{', '.join(sorted(pending))}")
    updated: list[Path] = []
    for path, metadata, body in matches:
        metadata["status"] = "superseded"
        metadata["updated_at"] = utc_now().isoformat()
        write_markdown(path, metadata, body)
        updated.append(path)
    return updated


def update_fixed_record(
    root: Path,
    relative_path: str,
    *,
    entry_id: str,
    title: str,
    content: str,
    source_refs: list[str],
) -> Path:
    path = root / relative_path
    metadata, body = read_markdown(path)
    metadata["updated_at"] = utc_now().isoformat()
    metadata["source_refs"] = list(dict.fromkeys([*metadata.get("source_refs", []), *source_refs]))
    marker = f"## [{entry_id}] {title}"
    if marker in body:
        raise ValueError(f"Entry already exists: {entry_id}")
    body = f"{body.rstrip()}\n\n{marker}\n\n{content.strip()}\n"
    write_markdown(path, metadata, body)
    return path
