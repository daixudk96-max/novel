from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from novel_runtime.pipeline.postcheck import PostcheckIssue, PostcheckRunner

_SEVERITY_ORDER = {
    "none": 0,
    "minor": 1,
    "major": 2,
    "blocker": 3,
}


@dataclass(frozen=True, slots=True)
class AuditIssue:
    rule: str
    severity: str
    message: str
    location: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuditResult:
    chapter: int
    status: str
    severity: str
    recommended_action: str
    issues: list[AuditIssue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "status": self.status,
            "severity": self.severity,
            "recommended_action": self.recommended_action,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class ChapterAuditor:
    def __init__(self, postcheck_runner: PostcheckRunner | None = None) -> None:
        self._postcheck_runner = postcheck_runner or PostcheckRunner()

    def run(self, state, chapter_number: int, chapter_text: str) -> AuditResult:
        postcheck = self._postcheck_runner.run(state, chapter_number, chapter_text)
        issues = [self._from_postcheck_issue(issue) for issue in postcheck.issues]
        severity = self._result_severity(issues)
        if not postcheck.passed:
            return AuditResult(
                chapter=chapter_number,
                status="fail",
                severity=severity,
                recommended_action="revise_chapter",
                issues=issues,
            )
        return AuditResult(
            chapter=chapter_number,
            status="pass",
            severity=severity,
            recommended_action="proceed_to_snapshot",
            issues=issues,
        )

    def _from_postcheck_issue(self, issue: PostcheckIssue) -> AuditIssue:
        return AuditIssue(
            rule=issue.rule,
            severity=issue.severity,
            message=issue.message,
            location=dict(issue.location),
        )

    def _result_severity(self, issues: list[AuditIssue]) -> str:
        if not issues:
            return "none"
        return max(
            issues, key=lambda issue: _SEVERITY_ORDER.get(issue.severity, -1)
        ).severity


__all__ = ["AuditIssue", "AuditResult", "ChapterAuditor"]
