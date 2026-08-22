from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import add_artifact
from .checkpoint import load_checkpoint, update_checkpoint
from .context import build_context, render_context
from .knowledge import KnowledgeIndex
from .migration import migrate_v4
from .models import ArtifactStatus, DatePrecision, TaskStatus
from .schools import add_school, load_school, submission_readiness, update_school
from .tasks import add_task, list_tasks, refresh_overview, update_task
from .validate import validate_vault
from .vault import find_vault, init_vault, supersede_records, update_fixed_record


def _root(value: str | None) -> Path:
    return find_vault(Path(value or "."))


def _json_or_text(value: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(render_context(value))


def _parse_list(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def cmd_init(args: argparse.Namespace) -> int:
    created = init_vault(Path(args.path), timezone=args.timezone, cycle=args.cycle)
    print(f"已创建 v5 学生工作区：{Path(args.path).resolve()}")
    print(f"创建 {len([item for item in created if item.suffix == ''])} 个目录和 {len([item for item in created if item.suffix])} 个文件")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = _root(args.path)
    _json_or_text(build_context(root, args.query or ""), args.json)
    return 0


def cmd_remember(args: argparse.Namespace) -> int:
    root = _root(args.path)
    kind = args.kind
    if kind == "insight":
        target = "用户画像.md"
    elif kind == "preference":
        target = "学生档案/约束与偏好.md"
    elif kind == "fact":
        target = f"学生档案/事实/{args.id}.md"
    else:
        folder_by_kind = {
            "material": "经历",
            "experience": "经历",
            "feeling": "感受",
            "thought": "思考",
            "relationship": "关系",
        }
        target = f"素材库/{folder_by_kind[kind]}/{args.id}.md"

    if kind in {"fact", "material", "experience", "feeling", "thought", "relationship"} and target.endswith(f"/{args.id}.md"):
        path = root / target
        if path.exists():
            raise ValueError(f"记录已存在：{target}")
        from .markdown import write_markdown
        from .models import RecordMeta, dumpable
        from .vault import utc_now

        record_type = "student_fact" if kind == "fact" else f"material_{kind}"
        metadata = RecordMeta(
            id=args.id,
            type=record_type,
            created_at=utc_now(),
            updated_at=utc_now(),
            source_refs=args.source_ref or [],
            confidence=args.confidence,
            supersedes=args.supersedes or [],
        )
        write_markdown(path, dumpable(metadata), f"# {args.title}\n\n{args.content.strip()}\n")
        if args.supersedes:
            try:
                supersede_records(root, args.supersedes)
            except ValueError:
                path.unlink()
                raise
    else:
        entry_id = args.id
        update_fixed_record(
            root,
            target,
            entry_id=entry_id,
            title=args.title,
            content=args.content,
            source_refs=args.source_ref or [],
        )
    print(f"已写入：{target}")
    return 0


def cmd_task_add(args: argparse.Namespace) -> int:
    root = _root(args.path)
    path = add_task(
        root,
        task_id=args.id,
        title=args.title,
        deadline=args.deadline,
        precision=DatePrecision(args.precision),
        task_type=args.type,
        next_action=args.next_action,
        source_refs=args.source_ref or [],
        school_id=args.school,
        application_round=args.round,
        deadline_timezone=args.deadline_timezone,
        deadline_source=args.deadline_source,
        deadline_checked_at=args.deadline_checked_at,
    )
    refresh_overview(root)
    print(f"已创建任务：{path.relative_to(root)}")
    return 0


def cmd_task_update(args: argparse.Namespace) -> int:
    root = _root(args.path)
    path = update_task(
        root,
        args.id,
        status=TaskStatus(args.status) if args.status else None,
        next_action=args.next_action,
        completion_evidence=args.completion_evidence,
        deadline=args.deadline,
        precision=DatePrecision(args.precision) if args.precision else None,
        deadline_timezone=args.deadline_timezone,
        deadline_source=args.deadline_source,
        deadline_checked_at=args.deadline_checked_at,
        reopen_reason=args.reopen_reason,
    )
    refresh_overview(root)
    if args.status in {TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value}:
        current = load_checkpoint(root)
        update_checkpoint(
            root,
            current_goal=None,
            active_task_ids=[task_id for task_id in current.active_task_ids if task_id != args.id],
            just_completed=list(dict.fromkeys([*current.just_completed, args.id])) if args.status == TaskStatus.COMPLETED.value else None,
            next_action="" if args.status in {TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value} else None,
            waiting_or_blocked="" if args.status in {TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value} else None,
            resume_files=None,
        )
    print(f"已更新任务：{path.relative_to(root)}")
    return 0


def cmd_task_list(args: argparse.Namespace) -> int:
    root = _root(args.path)
    refresh_overview(root)
    tasks = list_tasks(root, include_terminal=args.all)
    if not tasks:
        print("没有任务")
        return 0
    for task in tasks:
        deadline = task.deadline.isoformat(timespec="minutes") if task.deadline else "无截止"
        print(f"{task.id}\t{task.status.value}\t{deadline}\t{task.title}")
    return 0


def cmd_checkpoint_show(args: argparse.Namespace) -> int:
    root = _root(args.path)
    checkpoint = load_checkpoint(root)
    print(json.dumps(checkpoint.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


def cmd_checkpoint_update(args: argparse.Namespace) -> int:
    root = _root(args.path)
    path = update_checkpoint(
        root,
        current_goal=args.goal,
        active_task_ids=_parse_list(args.active_tasks),
        just_completed=_parse_list(args.just_completed),
        next_action=args.next_action,
        waiting_or_blocked=args.waiting,
        resume_files=_parse_list(args.resume_files),
    )
    print(f"已更新：{path.relative_to(root)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = _root(args.path)
    issues = validate_vault(root)
    if not issues:
        print("校验通过")
        return 0
    for issue in issues:
        print(f"{issue.level}: {issue.path.relative_to(root)}: {issue.message}")
    return 1 if any(issue.level == "error" for issue in issues) else 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = _root(args.path)
    issues = validate_vault(root)
    print(f"vault: {root}")
    print(f"embedding base url: {'已配置' if __import__('os').environ.get('BRAIN_EMBEDDING_BASE_URL') else '未配置（关键词检索仍可用）'}")
    print(f"embedding model: {__import__('os').environ.get('BRAIN_EMBEDDING_MODEL', '未配置')}")
    if issues:
        for issue in issues:
            print(f"{issue.level}: {issue.path.relative_to(root)}: {issue.message}")
        return 1 if any(issue.level == "error" for issue in issues) else 0
    print("环境和 vault 基础校验通过")
    return 0


def cmd_hook_session_context(args: argparse.Namespace) -> int:
    try:
        root = _root(args.path)
        context = render_context(build_context(root))[:16000]
    except (FileNotFoundError, ValueError):
        context = "当前目录不是 v5 学生 vault；需要时运行 brain init。"
    print(json.dumps({"additionalContext": context}, ensure_ascii=False))
    return 0


def cmd_knowledge_import(args: argparse.Namespace) -> int:
    root = _root(args.path)
    index = KnowledgeIndex(root)
    try:
        segments = index.import_transcript(
            Path(args.file),
            advisor=args.advisor,
            platform=args.platform,
            source_url=args.source_url,
            published_at=args.published_at,
            copyright_status=args.copyright_status,
            batch_id=args.batch_id,
            heading_level=args.heading_level,
            delimiter=args.delimiter,
            dry_run=args.dry_run,
        )
    finally:
        index.close()
    print(f"识别视频：{len(segments)}")
    for segment in segments[:20]:
        print(f"{segment.ordinal}. {segment.source_id} {segment.title}（第 {segment.start_line}-{segment.end_line} 行）")
    if args.dry_run:
        print("仅预览，未写入 knowledge/sources")
    return 0


def cmd_knowledge_index(args: argparse.Namespace) -> int:
    root = _root(args.path)
    index = KnowledgeIndex(root)
    try:
        count = index.index_sources(allow_remote_content=args.allow_remote_content)
    finally:
        index.close()
    print(f"已索引片段：{count}")
    return 0


def cmd_knowledge_search(args: argparse.Namespace) -> int:
    root = _root(args.path)
    index = KnowledgeIndex(root)
    try:
        results = index.search(args.query, limit=args.limit, allow_remote_query=args.allow_remote_query)
    finally:
        index.close()
    if not results:
        print("没有找到相关片段")
        return 0
    for result in results:
        print(f"[{result.match_type}] {result.citation} {result.title} score={result.score:.5f}")
        print(f"来源：{result.source_path}")
        print(result.content)
        print()
    return 0


def cmd_migrate_v4(args: argparse.Namespace) -> int:
    report = migrate_v4(
        Path(args.source),
        Path(args.output),
        dry_run=args.dry_run,
        timezone=args.timezone,
        cycle=args.cycle,
    )
    print(report.render())
    if args.dry_run:
        print("仅预览，未写入目标目录")
    return 0


def cmd_school_add(args: argparse.Namespace) -> int:
    root = _root(args.path)
    path = add_school(
        root,
        school_id=args.id,
        school_name=args.name,
        application_round=args.round,
        intended_major=args.major,
        source_refs=args.source_ref or [],
    )
    print(f"已创建学校申请记录：{path.relative_to(root)}")
    return 0


def cmd_school_update(args: argparse.Namespace) -> int:
    root = _root(args.path)
    path = update_school(
        root,
        args.id,
        status=args.status,
        application_round=args.round,
        missing_items=_parse_list(args.missing_items),
        next_actions=_parse_list(args.next_actions),
        final_artifact_ids=_parse_list(args.final_artifacts),
        requirements_checked_at=args.requirements_checked_at,
        requirement_source=args.requirement_source,
        student_confirmed=args.student_confirmed,
        submitted_at=args.submitted_at,
        submission_evidence=args.submission_evidence,
    )
    print(f"已更新学校申请记录：{path.relative_to(root)}")
    return 0


def cmd_school_status(args: argparse.Namespace) -> int:
    root = _root(args.path)
    meta, _ = load_school(root / "申请追踪/学校" / f"{args.id}.md")
    ready, reasons = submission_readiness(root, meta)
    print(json.dumps({**meta.model_dump(mode="json", exclude_none=True), "submission_ready": ready, "readiness_issues": reasons}, ensure_ascii=False, indent=2))
    return 0


def cmd_artifact_add(args: argparse.Namespace) -> int:
    root = _root(args.path)
    content = Path(args.content_file).read_text(encoding="utf-8") if args.content_file else args.content
    path = add_artifact(
        root,
        artifact_id=args.id,
        artifact_type=args.type,
        version=args.version,
        status=ArtifactStatus(args.status),
        content=content,
        target_school_id=args.school,
        prompt=args.prompt,
        limit=args.limit,
        limit_unit=args.limit_unit,
        source_material_ids=args.source_material or [],
        student_confirmed=args.student_confirmed,
    )
    print(f"已创建申请材料：{path.relative_to(root)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="brain", description="学生申请第二大脑本地工具")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="创建 v5 学生工作区")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--timezone", default="Asia/Shanghai")
    init.add_argument("--cycle", help="申请季开始月份，例如 2027-08")
    init.set_defaults(func=cmd_init)

    context = sub.add_parser("context", help="获取时间、checkpoint 和相关记录")
    context.add_argument("--path")
    context.add_argument("--query", default="")
    context.add_argument("--json", action="store_true")
    context.set_defaults(func=cmd_context)

    remember = sub.add_parser("remember", help="写入一条学生记录")
    remember.add_argument("--path")
    remember.add_argument("--kind", choices=["fact", "material", "experience", "feeling", "thought", "relationship", "insight", "preference"], required=True)
    remember.add_argument("--id", required=True)
    remember.add_argument("--title", required=True)
    remember.add_argument("--content", required=True)
    remember.add_argument("--source-ref", action="append")
    remember.add_argument("--confidence", default="confirmed")
    remember.add_argument("--supersedes", action="append", help="使指定旧记录失效")
    remember.set_defaults(func=cmd_remember)

    task = sub.add_parser("task", help="管理申请任务")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    add = task_sub.add_parser("add")
    add.add_argument("--path")
    add.add_argument("--id", required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--deadline")
    add.add_argument("--precision", choices=[item.value for item in DatePrecision], default="unknown")
    add.add_argument("--type", default="general")
    add.add_argument("--next-action")
    add.add_argument("--source-ref", action="append")
    add.add_argument("--school")
    add.add_argument("--round")
    add.add_argument("--deadline-timezone", help="学校或事项原始截止时区")
    add.add_argument("--deadline-source", help="官方 deadline 来源 URL 或文件")
    add.add_argument("--deadline-checked-at", help="核验时间 ISO 8601")
    add.set_defaults(func=cmd_task_add)
    update = task_sub.add_parser("update")
    update.add_argument("--path")
    update.add_argument("--id", required=True)
    update.add_argument("--status", choices=[item.value for item in TaskStatus])
    update.add_argument("--next-action")
    update.add_argument("--completion-evidence")
    update.add_argument("--deadline")
    update.add_argument("--precision", choices=[item.value for item in DatePrecision])
    update.add_argument("--deadline-timezone")
    update.add_argument("--deadline-source")
    update.add_argument("--deadline-checked-at")
    update.add_argument("--reopen-reason")
    update.set_defaults(func=cmd_task_update)
    listing = task_sub.add_parser("list")
    listing.add_argument("--path")
    listing.add_argument("--all", action="store_true")
    listing.set_defaults(func=cmd_task_list)

    checkpoint = sub.add_parser("checkpoint", help="管理当前会话状态")
    checkpoint_sub = checkpoint.add_subparsers(dest="checkpoint_command", required=True)
    show = checkpoint_sub.add_parser("show")
    show.add_argument("--path")
    show.set_defaults(func=cmd_checkpoint_show)
    update = checkpoint_sub.add_parser("update")
    update.add_argument("--path")
    update.add_argument("--goal")
    update.add_argument("--active-tasks")
    update.add_argument("--just-completed")
    update.add_argument("--next-action")
    update.add_argument("--waiting")
    update.add_argument("--resume-files")
    update.set_defaults(func=cmd_checkpoint_update)

    validate = sub.add_parser("validate", help="校验 vault")
    validate.add_argument("--path")
    validate.set_defaults(func=cmd_validate)
    doctor = sub.add_parser("doctor", help="检查本地环境")
    doctor.add_argument("--path")
    doctor.set_defaults(func=cmd_doctor)

    hook = sub.add_parser("hook", help="ZCode 等客户端的只读 hook 输出")
    hook_sub = hook.add_subparsers(dest="hook_command", required=True)
    hook_context = hook_sub.add_parser("session-context")
    hook_context.add_argument("--path")
    hook_context.set_defaults(func=cmd_hook_session_context)

    knowledge = sub.add_parser("knowledge", help="管理顾问知识库")
    knowledge_sub = knowledge.add_subparsers(dest="knowledge_command", required=True)
    knowledge_import = knowledge_sub.add_parser("import", help="导入合并转写稿")
    knowledge_import.add_argument("file")
    knowledge_import.add_argument("--path")
    knowledge_import.add_argument("--advisor", default="unknown")
    knowledge_import.add_argument("--platform")
    knowledge_import.add_argument("--source-url")
    knowledge_import.add_argument("--published-at")
    knowledge_import.add_argument("--copyright-status", default="undetermined")
    knowledge_import.add_argument("--batch-id", help="导入批次 ID，用于生成稳定且不冲突的来源 ID")
    knowledge_import.add_argument("--heading-level", type=int, choices=[1, 2, 3], default=1)
    knowledge_import.add_argument("--delimiter", help="视频之间的精确分隔行")
    knowledge_import.add_argument("--dry-run", action="store_true")
    knowledge_import.set_defaults(func=cmd_knowledge_import)
    knowledge_index = knowledge_sub.add_parser("index", help="建立或更新检索索引")
    knowledge_index.add_argument("--path")
    knowledge_index.add_argument("--allow-remote-content", action="store_true", help="允许把顾问转写片段发送到配置的云端 embedding API")
    knowledge_index.set_defaults(func=cmd_knowledge_index)
    knowledge_search = knowledge_sub.add_parser("search", help="搜索顾问知识片段")
    knowledge_search.add_argument("query")
    knowledge_search.add_argument("--path")
    knowledge_search.add_argument("--limit", type=int, default=5)
    knowledge_search.add_argument("--allow-remote-query", action="store_true", help="确认查询已去个人信息后使用云端向量检索")
    knowledge_search.set_defaults(func=cmd_knowledge_search)

    migrate = sub.add_parser("migrate-v4", help="非破坏迁移旧 v4 vault")
    migrate.add_argument("source")
    migrate.add_argument("--output", required=True)
    migrate.add_argument("--dry-run", action="store_true")
    migrate.add_argument("--timezone", default="Asia/Shanghai")
    migrate.add_argument("--cycle")
    migrate.set_defaults(func=cmd_migrate_v4)

    school = sub.add_parser("school", help="管理逐校申请状态")
    school_sub = school.add_subparsers(dest="school_command", required=True)
    school_add = school_sub.add_parser("add")
    school_add.add_argument("--path")
    school_add.add_argument("--id", required=True)
    school_add.add_argument("--name", required=True)
    school_add.add_argument("--round")
    school_add.add_argument("--major")
    school_add.add_argument("--source-ref", action="append")
    school_add.set_defaults(func=cmd_school_add)
    school_update = school_sub.add_parser("update")
    school_update.add_argument("--path")
    school_update.add_argument("--id", required=True)
    school_update.add_argument("--status")
    school_update.add_argument("--round")
    school_update.add_argument("--missing-items")
    school_update.add_argument("--next-actions")
    school_update.add_argument("--final-artifacts")
    school_update.add_argument("--requirements-checked-at")
    school_update.add_argument("--requirement-source")
    school_update.add_argument("--student-confirmed", action=argparse.BooleanOptionalAction, default=None)
    school_update.add_argument("--submitted-at")
    school_update.add_argument("--submission-evidence")
    school_update.set_defaults(func=cmd_school_update)
    school_status = school_sub.add_parser("status")
    school_status.add_argument("--path")
    school_status.add_argument("--id", required=True)
    school_status.set_defaults(func=cmd_school_status)

    artifact = sub.add_parser("artifact", help="创建版本化申请材料")
    artifact_sub = artifact.add_subparsers(dest="artifact_command", required=True)
    artifact_add = artifact_sub.add_parser("add")
    artifact_add.add_argument("--path")
    artifact_add.add_argument("--id", required=True)
    artifact_add.add_argument("--type", choices=["commonapp", "activity", "honor", "essay", "recommendation"], required=True)
    artifact_add.add_argument("--version", type=int, default=1)
    artifact_add.add_argument("--status", choices=[item.value for item in ArtifactStatus], default=ArtifactStatus.DRAFT.value)
    content_group = artifact_add.add_mutually_exclusive_group(required=True)
    content_group.add_argument("--content")
    content_group.add_argument("--content-file")
    artifact_add.add_argument("--school")
    artifact_add.add_argument("--prompt")
    artifact_add.add_argument("--limit", type=int)
    artifact_add.add_argument("--limit-unit")
    artifact_add.add_argument("--source-material", action="append")
    artifact_add.add_argument("--student-confirmed", action="store_true")
    artifact_add.set_defaults(func=cmd_artifact_add)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
