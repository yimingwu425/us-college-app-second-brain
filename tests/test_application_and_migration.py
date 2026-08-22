from __future__ import annotations

from pathlib import Path

import pytest

from college_brain.artifacts import add_artifact
from college_brain.migration import migrate_v4
from college_brain.models import ArtifactStatus
from college_brain.schools import add_school, load_school, submission_readiness, update_school
from college_brain.validate import validate_vault
from college_brain.vault import init_vault
from college_brain.markdown import read_markdown


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    init_vault(root, timezone="Asia/Shanghai", cycle="2027-08")
    return root


def test_final_artifact_requires_student_confirmation(vault: Path) -> None:
    with pytest.raises(ValueError, match="学生确认"):
        add_artifact(
            vault,
            artifact_id="brown-why",
            artifact_type="essay",
            version=1,
            status=ArtifactStatus.FINAL,
            content="draft",
            target_school_id="brown",
            prompt="Why Brown?",
            limit=250,
            limit_unit="words",
            source_material_ids=["material-market"],
            student_confirmed=False,
        )


def test_school_submission_readiness_has_explicit_conditions(vault: Path) -> None:
    add_artifact(
        vault,
        artifact_id="brown-why",
        artifact_type="essay",
        version=1,
        status=ArtifactStatus.FINAL,
        content="final essay",
        target_school_id="brown",
        prompt="Why Brown?",
        limit=250,
        limit_unit="words",
        source_material_ids=["material-market"],
        student_confirmed=True,
    )
    add_school(vault, school_id="brown", school_name="Brown University", application_round="ED", intended_major="Urban Studies", source_refs=[])
    update_school(
        vault,
        "brown",
        status="准备中",
        application_round=None,
        missing_items=[],
        next_actions=[],
        final_artifact_ids=["brown-why"],
        requirements_checked_at="2026-08-22T12:00:00Z",
        requirement_source="https://admission.brown.edu/",
        student_confirmed=True,
        submitted_at=None,
        submission_evidence=None,
    )
    school, _ = load_school(vault / "申请追踪/学校/brown.md")
    ready, reasons = submission_readiness(vault, school)
    assert ready
    assert reasons == []


def test_school_is_not_ready_when_final_artifact_is_missing(vault: Path) -> None:
    add_school(vault, school_id="brown", school_name="Brown University", application_round="ED", intended_major=None, source_refs=[])
    update_school(
        vault,
        "brown",
        status="准备中",
        application_round=None,
        missing_items=[],
        next_actions=[],
        final_artifact_ids=["missing-final"],
        requirements_checked_at="2026-08-22T12:00:00Z",
        requirement_source="https://admission.brown.edu/",
        student_confirmed=True,
        submitted_at=None,
        submission_evidence=None,
    )
    school, _ = load_school(vault / "申请追踪/学校/brown.md")
    ready, reasons = submission_readiness(vault, school)
    assert not ready
    assert any("找不到" in reason for reason in reasons)


def test_submission_requires_evidence(vault: Path) -> None:
    add_school(vault, school_id="brown", school_name="Brown University", application_round=None, intended_major=None, source_refs=[])
    with pytest.raises(ValueError, match="submission-evidence"):
        update_school(
            vault,
            "brown",
            status="已提交",
            application_round=None,
            missing_items=None,
            next_actions=None,
            final_artifact_ids=None,
            requirements_checked_at=None,
            requirement_source=None,
            student_confirmed=None,
            submitted_at="2026-10-30T12:00:00Z",
            submission_evidence=None,
        )


def test_submitted_status_requires_timestamp(vault: Path) -> None:
    add_school(vault, school_id="brown", school_name="Brown University", application_round=None, intended_major=None, source_refs=[])
    with pytest.raises(ValueError, match="submitted-at"):
        update_school(
            vault,
            "brown",
            status="已提交",
            application_round=None,
            missing_items=None,
            next_actions=None,
            final_artifact_ids=None,
            requirements_checked_at=None,
            requirement_source=None,
            student_confirmed=None,
            submitted_at=None,
            submission_evidence="学生确认邮件",
        )


def test_v4_migration_is_non_destructive_and_valid(tmp_path: Path) -> None:
    old = tmp_path / "old"
    old.mkdir()
    (old / "用户画像.md").write_text("# 用户画像\n\n喜欢城市观察。\n", encoding="utf-8")
    (old / "本体画像").mkdir()
    (old / "本体画像/00-核心身份.md").write_text("# 核心身份\n\n11 年级。\n", encoding="utf-8")
    (old / "申请追踪/每所学校进度").mkdir(parents=True)
    (old / "申请追踪/每所学校进度/Brown.md").write_text(
        "# Brown 进度\n\n- 轮次：ED\n- 材料缺口：Why School 具体点、推荐信人选\n- 下一步：核对官网要求\n",
        encoding="utf-8",
    )
    (old / "申请追踪/Deadline总览.md").write_text(
        "| 事项 | 日期 | 学校/系统 | 状态 | 备注 |\n| --- | --- | --- | --- | --- |\n| 主文书 | 2026-10-01 | Common App | 进行中 | |\n",
        encoding="utf-8",
    )
    before = {path.relative_to(old).as_posix(): path.read_bytes() for path in old.rglob("*") if path.is_file()}
    target = tmp_path / "new"
    preview = migrate_v4(old, target, dry_run=True, cycle="2027-08")
    assert preview.mappings
    assert not target.exists()
    report = migrate_v4(old, target, cycle="2027-08")
    after = {path.relative_to(old).as_posix(): path.read_bytes() for path in old.rglob("*") if path.is_file()}
    assert before == after
    assert report.mappings
    migrated_tasks = list((target / "申请追踪/任务").glob("*.md"))
    assert migrated_tasks
    task_meta, _ = read_markdown(migrated_tasks[0])
    assert task_meta["deadline_precision"] == "date_only"
    assert task_meta["deadline"] == "2026-10-01T00:00:00+08:00"
    school_meta, _ = read_markdown(target / "申请追踪/学校/brown.md")
    assert school_meta["application_round"] == "ED"
    assert school_meta["missing_items"] == ["Why School 具体点", "推荐信人选"]
    assert not [issue for issue in validate_vault(target) if issue.level == "error"]
