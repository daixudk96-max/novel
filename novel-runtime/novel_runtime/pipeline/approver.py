from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .auditor import AuditIssue, AuditResult
from .reviser import RevisionResult


@dataclass(frozen=True, slots=True)
class ApprovalResult:
    chapter: int
    status: str
    reason: str
    conditions: list[str]


class ChapterApprover:
    def approve(
        self, audit: AuditResult, revision: RevisionResult | None = None
    ) -> ApprovalResult:
        if audit.status == "pass":
            return ApprovalResult(
                chapter=audit.chapter,
                status="approved",
                reason="audit passed and chapter is ready for snapshot",
                conditions=[],
            )

        if not revision:
            return ApprovalResult(
                chapter=audit.chapter,
                status="rejected",
                reason="audit failed and no revision was provided",
                conditions=["provide a revision that addresses the audit issues"],
            )

        issues_addressed = self._issues_addressed(audit, revision)
        if not issues_addressed:
            return ApprovalResult(
                chapter=audit.chapter,
                status="rejected",
                reason="audit failed and revision addressed no issues",
                conditions=["address at least one audit issue before snapshot"],
            )

        return ApprovalResult(
            chapter=audit.chapter,
            status="conditionally_approved",
            reason=(
                f"audit failed, but revision addressed {len(issues_addressed)} issues"
            ),
            conditions=[
                f"confirm {issue['rule']} remains resolved before snapshot"
                for issue in issues_addressed
            ],
        )

    def _issues_addressed(
        self, audit: AuditResult, revision: RevisionResult | None
    ) -> list[dict[str, Any]]:
        if not revision:
            return []
        audit_issue_keys = {self._issue_key_from_audit(issue) for issue in audit.issues}
        return [
            dict(issue)
            for issue in revision.issues_addressed
            if self._issue_key_from_revision(issue) in audit_issue_keys
        ]

    def _issue_key_from_audit(self, issue: AuditIssue) -> tuple[str, str]:
        return self._issue_key(issue.rule, issue.message)

    def _issue_key_from_revision(self, issue: dict[str, Any]) -> tuple[str, str]:
        return self._issue_key(str(issue["rule"]), str(issue["message"]))

    def _issue_key(self, rule: str, message: str) -> tuple[str, str]:
        return (rule, message)


__all__ = ["ApprovalResult", "ChapterApprover"]
