from __future__ import annotations

import importlib

import pytest


def test_route_returns_pass_decision_for_passing_audit() -> None:
    auditor_module = importlib.import_module("novel_runtime.pipeline.auditor")
    router_module = _load_router_module()

    audit = auditor_module.AuditResult(
        chapter=1,
        status="pass",
        severity="none",
        recommended_action="proceed_to_snapshot",
        issues=[],
    )

    result = router_module.ChapterRouter().route(audit)

    assert isinstance(result, router_module.RoutingDecision)
    assert result.action == "pass"
    assert result.reason == "audit passed with no blocking issues"
    assert result.audit_summary == {
        "chapter": 1,
        "status": "pass",
        "severity": "none",
        "recommended_action": "proceed_to_snapshot",
        "issue_count": 0,
        "blocker_issue_count": 0,
    }


def test_route_returns_revise_decision_for_major_audit_failure() -> None:
    audit = _build_audit_result(
        severity="major",
        issues=[_build_issue(rule="continuity-gap", severity="major")],
    )

    result = _load_router_module().ChapterRouter().route(audit)

    assert result.action == "revise"
    assert result.reason == "audit failed with major severity"
    assert result.audit_summary == {
        "chapter": 1,
        "status": "fail",
        "severity": "major",
        "recommended_action": "revise_chapter",
        "issue_count": 1,
        "blocker_issue_count": 0,
    }


def test_route_returns_rewrite_decision_for_blocker_failure_below_escalation_threshold() -> (
    None
):
    audit = _build_audit_result(
        severity="blocker",
        issues=[
            _build_issue(rule="name-mismatch", severity="blocker"),
            _build_issue(rule="timeline-break", severity="blocker"),
        ],
    )

    result = _load_router_module().ChapterRouter().route(audit)

    assert result.action == "rewrite"
    assert result.reason == "audit failed with blocker severity across 2 blocker issues"
    assert result.audit_summary == {
        "chapter": 1,
        "status": "fail",
        "severity": "blocker",
        "recommended_action": "revise_chapter",
        "issue_count": 2,
        "blocker_issue_count": 2,
    }


def test_route_returns_escalate_decision_for_three_or_more_blocker_issues() -> None:
    audit = _build_audit_result(
        severity="blocker",
        issues=[
            _build_issue(rule="name-mismatch", severity="blocker"),
            _build_issue(rule="timeline-break", severity="blocker"),
            _build_issue(rule="continuity-hole", severity="blocker"),
        ],
    )

    result = _load_router_module().ChapterRouter().route(audit)

    assert result.action == "escalate"
    assert result.reason == "audit failed with 3 blocker issues and requires escalation"
    assert result.audit_summary == {
        "chapter": 1,
        "status": "fail",
        "severity": "blocker",
        "recommended_action": "revise_chapter",
        "issue_count": 3,
        "blocker_issue_count": 3,
    }


def _build_audit_result(*, severity: str, issues: list[object]):
    auditor_module = importlib.import_module("novel_runtime.pipeline.auditor")
    return auditor_module.AuditResult(
        chapter=1,
        status="fail",
        severity=severity,
        recommended_action="revise_chapter",
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


def _load_router_module():
    try:
        return importlib.import_module("novel_runtime.pipeline.router")
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.pipeline.router module is required for the chapter routing contract"
        )
