from __future__ import annotations

from pathlib import Path

import pytest

from college_brain.checkpoint import load_checkpoint, update_checkpoint
from college_brain.cli import main
from college_brain.context import build_context, related_files
from college_brain.markdown import read_markdown
from college_brain.models import DatePrecision, TaskStatus
from college_brain.tasks import add_task, list_tasks, task_timing, update_task
from college_brain.validate import validate_vault
from college_brain.vault import init_vault


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    init_vault(root, timezone="Asia/Shanghai", cycle="2027-08")
    return root


def test_init_creates_valid_vault(vault: Path) -> None:
    assert not validate_vault(vault)
    assert (vault / "状态/当前.md").is_file()
    assert (vault / "申请追踪/任务").is_dir()


def test_completed_task_disappears_from_context_and_updates_checkpoint(vault: Path) -> None:
    add_task(
        vault,
        task_id="submit-essay",
        title="提交文书",
        deadline="2026-08-20T23:59:00+08:00",
        precision=DatePrecision.EXACT,
        task_type="essay",
        next_action="提交",
        source_refs=["student:2026-08-18"],
        school_id=None,
        application_round=None,
    )
    update_checkpoint(
        vault,
        current_goal="提交文书",
        active_task_ids=["submit-essay"],
        just_completed=[],
        next_action="提交",
        waiting_or_blocked="",
        resume_files=[],
    )
    assert main([
        "task", "update", "--path", str(vault), "--id", "submit-essay",
        "--status", "已完成", "--completion-evidence", "学生确认昨天已提交",
    ]) == 0
    assert build_context(vault)["open_tasks"] == []
    checkpoint = load_checkpoint(vault)
    assert "submit-essay" not in checkpoint.active_task_ids
    assert "submit-essay" in checkpoint.just_completed
    assert list((vault / "会话").rglob("*.md"))


def test_completion_requires_evidence(vault: Path) -> None:
    add_task(
        vault,
        task_id="sat",
        title="SAT 报名",
        deadline=None,
        precision=DatePrecision.UNKNOWN,
        task_type="test",
        next_action=None,
        source_refs=[],
        school_id=None,
        application_round=None,
    )
    with pytest.raises(ValueError, match="completion-evidence"):
        update_task(vault, "sat", status=TaskStatus.COMPLETED, next_action=None, completion_evidence=None, deadline=None, precision=None)


def test_superseded_record_is_not_retrieved(vault: Path) -> None:
    assert main(["remember", "--path", str(vault), "--kind", "fact", "--id", "old-hours", "--title", "旧时长", "--content", "社团每周十小时"] ) == 0
    assert main(["remember", "--path", str(vault), "--kind", "fact", "--id", "new-hours", "--title", "修正时长", "--content", "社团每周三小时", "--supersedes", "old-hours"] ) == 0
    old_meta, _ = read_markdown(vault / "学生档案/事实/old-hours.md")
    assert old_meta["status"] == "superseded"
    assert "学生档案/事实/old-hours.md" not in related_files(vault, "每周十小时")
    assert "学生档案/事实/new-hours.md" in related_files(vault, "每周三小时")


def test_exact_deadline_requires_time(vault: Path) -> None:
    with pytest.raises(ValueError, match="date_only"):
        add_task(
            vault,
            task_id="bad-exact",
            title="学校截止",
            deadline="2026-11-01",
            precision=DatePrecision.EXACT,
            task_type="school",
            next_action=None,
            source_refs=[],
            school_id="brown",
            application_round="ED",
        )


def test_terminal_task_requires_reason_to_reopen(vault: Path) -> None:
    add_task(
        vault,
        task_id="submitted",
        title="提交材料",
        deadline=None,
        precision=DatePrecision.UNKNOWN,
        task_type="submission",
        next_action="提交",
        source_refs=[],
        school_id=None,
        application_round=None,
    )
    update_task(vault, "submitted", status=TaskStatus.COMPLETED, next_action=None, completion_evidence="学生确认", deadline=None, precision=None)
    with pytest.raises(ValueError, match="reopen-reason"):
        update_task(vault, "submitted", status=TaskStatus.IN_PROGRESS, next_action=None, completion_evidence=None, deadline=None, precision=None)
    update_task(vault, "submitted", status=TaskStatus.IN_PROGRESS, next_action="重新提交", completion_evidence=None, deadline=None, precision=None, reopen_reason="学生更正：尚未提交")
    assert list_tasks(vault)[0].status == TaskStatus.IN_PROGRESS


def test_failed_supersede_keeps_old_record(vault: Path) -> None:
    assert main(["remember", "--path", str(vault), "--kind", "fact", "--id", "old", "--title", "旧事实", "--content", "仍然有效"]) == 0
    assert main(["remember", "--path", str(vault), "--kind", "fact", "--id", "new", "--title", "新事实", "--content", "无法落盘", "--supersedes", "missing"]) == 2
    old_meta, _ = read_markdown(vault / "学生档案/事实/old.md")
    assert old_meta["status"] == "active"
    assert not (vault / "学生档案/事实/new.md").exists()


def test_context_contains_live_time_and_timezone(vault: Path) -> None:
    context = build_context(vault)
    assert context["now"].endswith("+08:00")
    assert context["timezone"] == "Asia/Shanghai"
    assert context["application_cycle_start"] == "2027-08"
