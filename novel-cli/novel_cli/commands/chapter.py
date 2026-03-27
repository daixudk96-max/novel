from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Never

import click
from novel_runtime.llm.provider import build_route_a_provider
from novel_runtime.pipeline.assistant_result_validator import AssistantResultValidator
from novel_runtime.pipeline.approver import ChapterApprover
from novel_runtime.pipeline.auditor import AuditIssue, AuditResult, ChapterAuditor
from novel_runtime.pipeline.drafter import ChapterDraft, ChapterDrafter
from novel_runtime.pipeline.guider import ChapterGuider, first_active_world_entity
from novel_runtime.pipeline.postcheck import PostcheckRunner
from novel_runtime.pipeline.reviser import ChapterReviser, RevisionResult
from novel_runtime.pipeline.router import ChapterRouter
from novel_runtime.pipeline.settler import AlreadySettledError, ChapterSettler
from novel_runtime.state.canonical import CanonicalState

from novel_cli.commands.project import _emit, _fail, _resolve_project_dir


@click.group(name="chapter")
def chapter_group() -> None:
    pass


@chapter_group.command("draft")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option("--json", "json_output", is_flag=True)
def draft_chapter(chapter_number: int, json_output: bool) -> None:
    state, project_dir = _load_state()
    try:
        _require_draft_entity(state, chapter_number)
        draft = _build_chapter_drafter().draft(state, chapter_number)
    except ValueError as exc:
        _raise_fail(str(exc), json_output)

    chapter_path = project_dir / "chapters" / f"chapter_{chapter_number}.md"

    chapter_path.parent.mkdir(parents=True, exist_ok=True)
    chapter_path.write_text(draft.content, encoding="utf-8")
    _upsert_chapter(state, draft)
    state.save(project_dir)

    payload = {
        "chapter": draft.chapter,
        "title": draft.title,
        "status": draft.status,
        "path": str(chapter_path.resolve()),
        "summary": draft.summary,
    }
    _emit(
        payload,
        f"Drafted chapter {chapter_number} at {chapter_path.resolve()}",
        json_output,
    )


@chapter_group.command("guide")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option("--json", "json_output", is_flag=True)
def guide_chapter(chapter_number: int, json_output: bool) -> None:
    state, _ = _load_state()
    try:
        payload = {
            "ok": True,
            "command": "chapter guide",
            "version": "novel-cli-agent/v1",
            "warnings": [],
            "recommended_action": "chapter verify-guided-result",
            "data": ChapterGuider().guide(state, chapter_number),
        }
    except ValueError as exc:
        _raise_fail(str(exc), json_output)

    _emit(payload, _format_guidance_text(payload), json_output)


@chapter_group.command("settle")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--settlement-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--text-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def settle_chapter(
    chapter_number: int,
    settlement_file: Path,
    text_file: Path,
    json_output: bool,
) -> None:
    state, project_dir = _load_state()
    settlement_data = _load_json_object(settlement_file, "settlement file", json_output)
    chapter_text = _read_text_file(text_file)

    try:
        ChapterSettler().settle(state, chapter_number, chapter_text, settlement_data)
    except (AlreadySettledError, ValueError) as exc:
        _raise_fail(str(exc), json_output)
    else:
        state.save(project_dir)
        chapter = _get_chapter(state, chapter_number)
        assert chapter is not None
        payload = {"chapter": chapter_number, "status": chapter["status"]}
        _emit(payload, f"Settled chapter {chapter_number}", json_output)


@chapter_group.command("postcheck")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--text-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def postcheck_chapter(chapter_number: int, text_file: Path, json_output: bool) -> None:
    state, _ = _load_state()
    if _get_chapter(state, chapter_number) is None:
        _raise_fail(f"chapter '{chapter_number}' not found", json_output)

    result = PostcheckRunner().run(state, chapter_number, _read_text_file(text_file))
    payload = {
        "chapter": chapter_number,
        "passed": result.passed,
        "issues": [issue.to_dict() for issue in result.issues],
    }
    text = _format_postcheck_text(payload)
    _emit(payload, text, json_output)


@chapter_group.command("audit")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--text-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def audit_chapter(chapter_number: int, text_file: Path, json_output: bool) -> None:
    state, _ = _load_state()
    if _get_chapter(state, chapter_number) is None:
        _raise_fail(f"chapter '{chapter_number}' not found", json_output)

    result = ChapterAuditor().run(state, chapter_number, _read_text_file(text_file))
    payload = result.to_dict()
    text = _format_audit_text(payload)
    _emit(payload, text, json_output)
    if result.status == "fail":
        raise SystemExit(1)


@chapter_group.command("route")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--audit-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def route_chapter(chapter_number: int, audit_file: Path, json_output: bool) -> None:
    state, _ = _load_state()
    if _get_chapter(state, chapter_number) is None:
        _raise_fail(f"chapter '{chapter_number}' not found", json_output)

    audit = _load_audit_result(audit_file, json_output)
    _validate_audit_chapter(audit, chapter_number, json_output)
    decision = _route_chapter_audit(audit)
    payload = {
        "action": decision.action,
        "reason": decision.reason,
        "audit_summary": decision.audit_summary,
    }
    text = _format_route_text(payload)
    _emit(payload, text, json_output)
    if decision.action in {"rewrite", "escalate"}:
        raise SystemExit(1)


@chapter_group.command("revise")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--text-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--audit-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def revise_chapter(
    chapter_number: int,
    text_file: Path,
    audit_file: Path,
    json_output: bool,
) -> None:
    state, project_dir = _load_state()
    if _get_chapter(state, chapter_number) is None:
        _raise_fail(f"chapter '{chapter_number}' not found", json_output)

    chapter_text = _read_text_file(text_file)
    audit = _load_audit_result(audit_file, json_output)
    _validate_audit_chapter(audit, chapter_number, json_output)
    decision = _route_chapter_audit(audit)

    if decision.action == "pass":
        payload = {
            "chapter": chapter_number,
            "routing_action": decision.action,
            "reason": decision.reason,
        }
        _emit(payload, f"No revision needed for chapter {chapter_number}", json_output)
        return

    if decision.action != "revise":
        payload = {
            "action": decision.action,
            "reason": decision.reason,
            "audit_summary": decision.audit_summary,
        }
        _emit(payload, _format_route_text(payload), json_output)
        raise SystemExit(1)

    result = ChapterReviser().revise(chapter_number, chapter_text, audit.issues)
    revised_path = project_dir / "chapters" / f"chapter_{chapter_number}_revised.md"
    revised_path.parent.mkdir(parents=True, exist_ok=True)
    revised_path.write_text(result.revised_text, encoding="utf-8")

    payload = {
        "chapter": result.chapter,
        "path": str(revised_path.resolve()),
        "revised_text": result.revised_text,
        "revision_log": result.revision_log,
        "issues_addressed": result.issues_addressed,
        "routing_action": decision.action,
    }
    _emit(
        payload,
        _format_revision_text(payload),
        json_output,
    )


@chapter_group.command("approve")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--audit-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--revision-file",
    required=False,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def approve_chapter(
    chapter_number: int,
    audit_file: Path,
    revision_file: Path | None,
    json_output: bool,
) -> None:
    state, _ = _load_state()
    if _get_chapter(state, chapter_number) is None:
        _raise_fail(f"chapter '{chapter_number}' not found", json_output)

    audit = _load_audit_result(audit_file, json_output)
    _validate_audit_chapter(audit, chapter_number, json_output)
    revision = None
    if revision_file is not None:
        revision = _load_revision_result(revision_file, json_output)
        _validate_revision_chapter(revision, chapter_number, json_output)

    result = ChapterApprover().approve(audit, revision)
    payload = {
        "chapter": result.chapter,
        "status": result.status,
        "reason": result.reason,
        "conditions": list(result.conditions),
    }
    _emit(payload, _format_approval_text(payload), json_output)
    if result.status == "rejected":
        raise SystemExit(1)


@chapter_group.command("verify-guided-result")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--manifest-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def verify_guided_result(
    chapter_number: int, manifest_file: Path, json_output: bool
) -> None:
    _resolve_project_dir()
    try:
        validated = AssistantResultValidator().validate(
            chapter_number=chapter_number,
            manifest_file=manifest_file,
        )
    except ValueError as exc:
        _raise_fail(str(exc), json_output)

    payload = {
        "ok": True,
        "command": "chapter verify-guided-result",
        "version": "novel-cli-agent/v1",
        "data": {
            "guidance_id": validated.guidance_id,
            "chapter": validated.chapter,
            "prose_path": str(validated.prose_path),
            "settlement_path": str(validated.settlement_path),
            "command_receipts": validated.command_receipts,
            "warnings": validated.warnings,
            "ready_for_cli_validation": validated.ready_for_cli_validation,
        },
        "warnings": validated.warnings,
        "recommended_action": "chapter settle",
    }
    text = _format_verify_guided_result_text(
        chapter_number=validated.chapter,
        guidance_id=validated.guidance_id,
    )
    _emit(payload, text, json_output)


def _load_state() -> tuple[CanonicalState, Path]:
    project_dir = _resolve_project_dir()
    return CanonicalState.load(project_dir), project_dir


def _build_chapter_drafter() -> ChapterDrafter:
    return ChapterDrafter(provider=build_route_a_provider())


def _require_draft_entity(state: CanonicalState, chapter_number: int) -> None:
    if first_active_world_entity(state) is not None:
        return
    raise ValueError(
        f"chapter {chapter_number} draft requires at least one active world entity"
    )


def _upsert_chapter(state: CanonicalState, draft: ChapterDraft) -> dict[str, object]:
    chapter_number = draft.chapter
    title = draft.title
    status = draft.status
    summary = draft.summary
    chapter = _get_chapter(state, chapter_number)
    if chapter is None:
        chapter = {
            "number": chapter_number,
            "title": title,
            "status": status,
            "summary": summary,
            "settled_at": "",
        }
        state.data["chapters"].append(chapter)
        state.data["chapters"].sort(key=lambda item: item["number"])
        return chapter

    chapter["title"] = title
    chapter["status"] = status
    chapter["summary"] = summary
    chapter["settled_at"] = ""
    return chapter


def _get_chapter(state: CanonicalState, chapter_number: int) -> dict | None:
    for chapter in state.data["chapters"]:
        if chapter["number"] == chapter_number:
            return chapter
    return None


def _load_json_object(path: Path, label: str, json_output: bool) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _raise_fail(f"invalid {label} JSON: {exc.msg}", json_output)

    if not isinstance(payload, dict):
        _raise_fail(f"{label} must decode to a JSON object", json_output)
    return payload


def _load_audit_result(path: Path, json_output: bool) -> AuditResult:
    payload = _load_json_object(path, "audit file", json_output)
    try:
        issues_payload = payload["issues"]
        assert isinstance(issues_payload, list)
        return AuditResult(
            chapter=int(payload["chapter"]),
            status=str(payload["status"]),
            severity=str(payload["severity"]),
            recommended_action=str(payload["recommended_action"]),
            issues=[_load_audit_issue(issue) for issue in issues_payload],
        )
    except (AssertionError, KeyError, TypeError, ValueError):
        _raise_fail(
            "invalid audit file JSON: expected audit result object", json_output
        )


def _load_revision_result(path: Path, json_output: bool) -> RevisionResult:
    payload = _load_json_object(path, "revision file", json_output)
    try:
        revision_log = payload["revision_log"]
        issues_addressed = payload["issues_addressed"]
        assert isinstance(revision_log, list)
        assert isinstance(issues_addressed, list)
        return RevisionResult(
            chapter=int(payload["chapter"]),
            revised_text=str(payload["revised_text"]),
            revision_log=[str(item) for item in revision_log],
            issues_addressed=[
                _load_revision_issue(issue) for issue in issues_addressed
            ],
        )
    except (AssertionError, KeyError, TypeError, ValueError):
        _raise_fail(
            "invalid revision file JSON: expected revision result object", json_output
        )


def _load_audit_issue(payload: object) -> AuditIssue:
    if not isinstance(payload, dict):
        raise TypeError("audit issue must be an object")
    return AuditIssue(
        rule=str(payload["rule"]),
        severity=str(payload["severity"]),
        message=str(payload["message"]),
        location=_load_issue_location(payload["location"]),
    )


def _load_revision_issue(payload: object) -> dict[str, Any]:
    return _load_audit_issue(payload).to_dict()


def _load_issue_location(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("issue location must be an object")
    return dict(payload)


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _route_chapter_audit(audit: AuditResult):
    return ChapterRouter().route(audit)


def _validate_audit_chapter(
    audit: AuditResult, chapter_number: int, json_output: bool
) -> None:
    if audit.chapter != chapter_number:
        _raise_fail(
            f"audit file chapter '{audit.chapter}' does not match --chapter '{chapter_number}'",
            json_output,
        )


def _validate_revision_chapter(
    revision: RevisionResult, chapter_number: int, json_output: bool
) -> None:
    if revision.chapter != chapter_number:
        _raise_fail(
            f"revision file chapter '{revision.chapter}' does not match --chapter '{chapter_number}'",
            json_output,
        )


def _format_postcheck_text(payload: dict[str, object]) -> str:
    issues = payload["issues"]
    assert isinstance(issues, list)
    lines = [
        f"Chapter: {payload['chapter']}",
        f"Passed: {'yes' if payload['passed'] else 'no'}",
    ]
    if not issues:
        lines.append("Issues: none")
        return "\n".join(lines)

    lines.append("Issues:")
    for issue in issues:
        assert isinstance(issue, dict)
        lines.append(f"- {issue['rule']} | {issue['severity']} | {issue['message']}")
    return "\n".join(lines)


def _format_audit_text(payload: dict[str, object]) -> str:
    issues = payload["issues"]
    assert isinstance(issues, list)
    lines = [
        f"Chapter: {payload['chapter']}",
        f"Status: {payload['status']}",
        f"Severity: {payload['severity']}",
        f"Recommended action: {payload['recommended_action']}",
    ]
    if not issues:
        lines.append("Issues: none")
        return "\n".join(lines)

    lines.append("Issues:")
    for issue in issues:
        assert isinstance(issue, dict)
        lines.append(f"- {issue['rule']} | {issue['severity']} | {issue['message']}")
    return "\n".join(lines)


def _format_route_text(payload: dict[str, object]) -> str:
    audit_summary = payload["audit_summary"]
    assert isinstance(audit_summary, dict)
    return "\n".join(
        (
            f"Chapter: {audit_summary['chapter']}",
            f"Action: {payload['action']}",
            f"Reason: {payload['reason']}",
        )
    )


def _format_revision_text(payload: dict[str, object]) -> str:
    issues_addressed = payload["issues_addressed"]
    assert isinstance(issues_addressed, list)
    return "\n".join(
        (
            f"Chapter: {payload['chapter']}",
            f"Action: {payload['routing_action']}",
            f"Issues addressed: {len(issues_addressed)}",
            f"Output path: {payload['path']}",
        )
    )


def _format_approval_text(payload: dict[str, object]) -> str:
    conditions = payload["conditions"]
    assert isinstance(conditions, list)
    lines = [
        f"Chapter: {payload['chapter']}",
        f"Status: {payload['status']}",
        f"Reason: {payload['reason']}",
    ]
    if not conditions:
        lines.append("Conditions: none")
        return "\n".join(lines)

    lines.append("Conditions:")
    for condition in conditions:
        lines.append(f"- {condition}")
    return "\n".join(lines)


def _format_verify_guided_result_text(*, chapter_number: int, guidance_id: str) -> str:
    return "\n".join(
        (
            f"Chapter: {chapter_number}",
            f"Guidance ID: {guidance_id}",
            "Ready for CLI validation: yes",
            "Recommended action: chapter settle",
        )
    )


def _format_guidance_text(payload: dict[str, object]) -> str:
    data = payload["data"]
    assert isinstance(data, dict)
    return "\n".join(
        (
            f"Chapter: {data['chapter']}",
            f"Route: {data['route']}",
            f"Guidance ID: {data['guidance_id']}",
            f"Recommended action: {payload['recommended_action']}",
        )
    )


def _raise_fail(message: str, json_output: bool) -> Never:
    _fail(message, json_output)
    raise AssertionError("unreachable")


__all__ = ["chapter_group"]
