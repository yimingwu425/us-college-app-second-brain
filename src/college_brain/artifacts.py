from __future__ import annotations

from pathlib import Path

from .markdown import write_markdown
from .models import ArtifactMeta, ArtifactStatus, dumpable
from .vault import utc_now


FOLDER_BY_TYPE = {
    "commonapp": "CommonApp",
    "activity": "活动列表",
    "honor": "荣誉列表",
    "essay": "文书",
    "recommendation": "推荐信",
}


def artifact_path(root: Path, artifact_type: str, artifact_id: str, version: int) -> Path:
    folder = FOLDER_BY_TYPE[artifact_type]
    return root / "申请材料" / folder / artifact_id / f"v{version:02d}.md"


def add_artifact(
    root: Path,
    *,
    artifact_id: str,
    artifact_type: str,
    version: int,
    status: ArtifactStatus,
    content: str,
    target_school_id: str | None,
    prompt: str | None,
    limit: int | None,
    limit_unit: str | None,
    source_material_ids: list[str],
    student_confirmed: bool,
) -> Path:
    path = artifact_path(root, artifact_type, artifact_id, version)
    if path.exists():
        raise ValueError(f"申请材料版本已存在：{path.relative_to(root)}")
    if status in {ArtifactStatus.FINAL, ArtifactStatus.SUBMITTED} and not student_confirmed:
        raise ValueError("最终版或已提交材料必须由学生确认")
    now = utc_now()
    meta = ArtifactMeta(
        id=f"artifact-{artifact_id}-v{version}",
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        version=version,
        status=status,
        target_school_id=target_school_id,
        prompt=prompt,
        limit=limit,
        limit_unit=limit_unit,
        source_material_ids=source_material_ids,
        student_confirmed=student_confirmed,
        supersedes_version=version - 1 if version > 1 else None,
        created_at=now,
        updated_at=now,
        source_refs=source_material_ids,
    )
    write_markdown(path, dumpable(meta), f"# {artifact_id} v{version}\n\n{content.strip()}\n")
    return path
