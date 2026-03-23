from __future__ import annotations

import inspect
import importlib
import json

import pytest


def test_approve_returns_structured_approval_result_for_passing_audit() -> None:
    approver_module = _load_approver_module()
    audit = _build_audit_result(status="pass", severity="minor", issues=[])

    result = approver_module.ChapterApprover().approve(audit)

    assert isinstance(result, approver_module.ApprovalResult)
    assert result.chapter == 1
    assert result.status == "approved"
    assert result.reason == "audit passed and chapter is ready for snapshot"
    assert result.conditions == []


def test_approve_returns_conditionally_approved_when_revision_addresses_failed_audit() -> (
    None
):
    approver_module = _load_approver_module()
    audit = _build_audit_result(
        status="fail",
        severity="major",
        issues=[
            _build_issue(rule="continuity-gap", severity="major"),
            _build_issue(rule="tone-drift", severity="minor"),
        ],
    )
    revision = _build_revision_result(
        issues_addressed=[
            {
                "rule": "continuity-gap",
                "severity": "major",
                "message": "continuity-gap needs attention",
                "location": {
                    "line": 1,
                    "start": 0,
                    "end": 5,
                    "excerpt": "continuity-gap",
                },
            },
            {
                "rule": "tone-drift",
                "severity": "minor",
                "message": "tone-drift needs attention",
                "location": {"line": 1, "start": 0, "end": 5, "excerpt": "tone-drift"},
            },
        ]
    )

    result = approver_module.ChapterApprover().approve(audit, revision)

    assert result.chapter == 1
    assert result.status == "conditionally_approved"
    assert result.reason == "audit failed, but revision addressed 2 issues"
    assert result.conditions == [
        "confirm continuity-gap remains resolved before snapshot",
        "confirm tone-drift remains resolved before snapshot",
    ]


def test_approve_returns_rejected_when_failed_audit_has_no_revision() -> None:
    approver_module = _load_approver_module()
    audit = _build_audit_result(
        status="fail",
        severity="blocker",
        issues=[_build_issue(rule="name-mismatch", severity="blocker")],
    )

    result = approver_module.ChapterApprover().approve(audit)

    assert result.chapter == 1
    assert result.status == "rejected"
    assert result.reason == "audit failed and no revision was provided"
    assert result.conditions == ["provide a revision that addresses the audit issues"]


def test_approve_returns_rejected_when_revision_addresses_zero_issues() -> None:
    approver_module = _load_approver_module()
    audit = _build_audit_result(
        status="fail",
        severity="major",
        issues=[_build_issue(rule="continuity-gap", severity="major")],
    )
    revision = _build_revision_result(issues_addressed=[])

    result = approver_module.ChapterApprover().approve(audit, revision)

    assert result.chapter == 1
    assert result.status == "rejected"
    assert result.reason == "audit failed and revision addressed no issues"
    assert result.conditions == ["address at least one audit issue before snapshot"]


def test_approve_rejects_revision_that_addresses_only_unrelated_issues() -> None:
    approver_module = _load_approver_module()
    audit = _build_audit_result(
        status="fail",
        severity="major",
        issues=[_build_issue(rule="continuity-gap", severity="major")],
    )
    revision = _build_revision_result(
        issues_addressed=[
            {
                "rule": "tone-drift",
                "severity": "minor",
                "message": "tone-drift needs attention",
                "location": {
                    "line": 1,
                    "start": 0,
                    "end": 5,
                    "excerpt": "tone-drift",
                },
            }
        ]
    )

    result = approver_module.ChapterApprover().approve(audit, revision)

    assert result.chapter == 1
    assert result.status == "rejected"
    assert result.reason == "audit failed and revision addressed no issues"
    assert result.conditions == ["address at least one audit issue before snapshot"]


def test_approve_locks_output_only_signature_and_defers_stateful_or_llm_steps() -> None:
    approver_module = _load_approver_module()

    assert list(
        inspect.signature(approver_module.ChapterApprover.approve).parameters
    ) == [
        "self",
        "audit",
        "revision",
    ], (
        "approve must stay output-only; canonical state writes, settler/postcheck, and LLM/interactive approval remain deferred"
    )


def test_approve_keeps_audit_and_revision_inputs_unchanged() -> None:
    approver_module = _load_approver_module()
    audit = _build_audit_result(
        status="fail",
        severity="major",
        issues=[_build_issue(rule="continuity-gap", severity="major")],
    )
    revision = _build_revision_result(
        issues_addressed=[
            {
                "rule": "continuity-gap",
                "severity": "major",
                "message": "continuity-gap needs attention",
                "location": {"line": 1, "start": 0, "end": 5, "excerpt": "gap"},
            }
        ]
    )
    before_audit = audit.to_dict()
    before_revision = json.loads(json.dumps(revision.issues_addressed, sort_keys=True))

    result = approver_module.ChapterApprover().approve(audit, revision)

    assert audit.to_dict() == before_audit
    assert (
        json.loads(json.dumps(revision.issues_addressed, sort_keys=True))
        == before_revision
    )
    assert result.conditions == [
        "confirm continuity-gap remains resolved before snapshot"
    ]


def _build_audit_result(*, status: str, severity: str, issues: list[object]):
    auditor_module = importlib.import_module("novel_runtime.pipeline.auditor")
    recommended_action = "proceed_to_snapshot" if status == "pass" else "revise_chapter"
    return auditor_module.AuditResult(
        chapter=1,
        status=status,
        severity=severity,
        recommended_action=recommended_action,
        issues=issues,
    )


def _build_issue(*, rule: str, severity: str):
    auditor_module = importlib.import_module("novel_runtime.pipeline.auditor")
    return auditor_module.AuditIssue(
        rule=rule,
        severity=severity,
        message=f"{rule} needs attention",
        location={"line": 1, "start": 0, "end": 5, "excerpt": rule},
    )


def _build_revision_result(*, issues_addressed: list[dict[str, object]]):
    reviser_module = importlib.import_module("novel_runtime.pipeline.reviser")
    return reviser_module.RevisionResult(
        chapter=1,
        revised_text="Updated chapter text.",
        revision_log=["Applied revision note."] if issues_addressed else [],
        issues_addressed=issues_addressed,
    )


def _load_approver_module():
    try:
        return importlib.import_module("novel_runtime.pipeline.approver")
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.pipeline.approver module is required for the chapter approve contract"
        )
