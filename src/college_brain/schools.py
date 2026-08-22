from __future__ import annotations

from pathlib import Path

from .markdown import read_markdown, write_markdown
from .models import ArtifactMeta, ArtifactStatus, SchoolApplicationMeta, dumpable
from .vault import utc_now


def school_path(root: Path, school_id: str) -> Path:
    return root / "申请追踪/学校" / f"{school_id}.md"


def add_school(
    root: Path,
    *,
    school_id: str,
    school_name: str,
    application_round: str | None,
    intended_major: str | None,
    source_refs: list[str],
) -> Path:
    path = school_path(root, school_id)
    if path.exists():
        raise ValueError(f"学校申请记录已存在：{school_id}")
    now = utc_now()
    meta = SchoolApplicationMeta(
        id=f"school-application-{school_id}",
        school_id=school_id,
        school_name=school_name,
        application_round=application_round,
        intended_major=intended_major,
        created_at=now,
        updated_at=now,
        source_refs=source_refs,
    )
    write_markdown(path, dumpable(meta), f"# {school_name} 申请状态\n")
    return path


def load_school(path: Path) -> tuple[SchoolApplicationMeta, str]:
    metadata, body = read_markdown(path)
    return SchoolApplicationMeta.model_validate(metadata), body


def _artifact_candidates(root: Path, meta: SchoolApplicationMeta, artifact_id: str) -> tuple[list[ArtifactMeta], list[str]]:
    candidates: list[ArtifactMeta] = []
    errors: list[str] = []
    for path in (root / "申请材料").rglob("*.md"):
        try:
            metadata, _ = read_markdown(path)
            if metadata.get("type") != "application_artifact":
                continue
            artifact = ArtifactMeta.model_validate(metadata)
        except (ValueError, TypeError) as exc:
            errors.append(f"材料无法解析：{path.relative_to(root)}（{exc}）")
            continue
        if artifact.artifact_id != artifact_id:
            continue
        if artifact.target_school_id not in {None, meta.school_id}:
            continue
        candidates.append(artifact)
    return sorted(candidates, key=lambda item: item.version, reverse=True), errors


def submission_readiness(root: Path, meta: SchoolApplicationMeta) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not meta.requirements_checked_at or not meta.requirement_source:
        reasons.append("官方要求尚未核验")
    if meta.missing_items:
        reasons.extend(f"缺少：{item}" for item in meta.missing_items)
    if not meta.student_confirmed:
        reasons.append("学生尚未确认提交")
    artifact_ids = set(meta.final_artifact_ids)
    if not artifact_ids:
        reasons.append("没有登记最终申请材料")
    found: set[str] = set()
    for artifact_id in sorted(artifact_ids):
        candidates, parse_errors = _artifact_candidates(root, meta, artifact_id)
        reasons.extend(parse_errors)
        if not candidates:
            reasons.append(f"找不到属于 {meta.school_id} 的申请材料：{artifact_id}")
            continue
        artifact = candidates[0]
        if artifact.status not in {ArtifactStatus.FINAL, ArtifactStatus.SUBMITTED} or not artifact.student_confirmed:
            reasons.append(f"材料未最终确认：{artifact.artifact_id} v{artifact.version}")
        else:
            found.add(artifact_id)
    for missing_id in sorted(artifact_ids - found):
        if not any(f"申请材料：{missing_id}" in reason for reason in reasons):
            reasons.append(f"找不到已确认最终材料：{missing_id}")
    return not reasons, reasons


def update_school(
    root: Path,
    school_id: str,
    *,
    status: str | None,
    application_round: str | None,
    missing_items: list[str] | None,
    next_actions: list[str] | None,
    final_artifact_ids: list[str] | None,
    requirements_checked_at: str | None,
    requirement_source: str | None,
    student_confirmed: bool | None,
    submitted_at: str | None,
    submission_evidence: str | None,
) -> Path:
    path = school_path(root, school_id)
    meta, body = load_school(path)
    changes = meta.model_dump()
    for key, value in {
        "status": status,
        "application_round": application_round,
        "missing_items": missing_items,
        "next_actions": next_actions,
        "final_artifact_ids": final_artifact_ids,
        "requirements_checked_at": requirements_checked_at,
        "requirement_source": requirement_source,
        "student_confirmed": student_confirmed,
        "submitted_at": submitted_at,
        "submission_evidence": submission_evidence,
    }.items():
        if value is not None:
            changes[key] = value
    if changes.get("status") == "已提交":
        if not changes.get("submitted_at"):
            raise ValueError("已提交状态需要 --submitted-at")
        if not changes.get("submission_evidence"):
            raise ValueError("已提交状态需要 --submission-evidence")
    elif submitted_at and not submission_evidence and not changes.get("submission_evidence"):
        raise ValueError("记录已提交需要 --submission-evidence")
    changes["updated_at"] = utc_now()
    updated = SchoolApplicationMeta.model_validate(changes)
    write_markdown(path, dumpable(updated), body)
    return path
