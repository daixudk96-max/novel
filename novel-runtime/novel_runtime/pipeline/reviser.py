from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .auditor import AuditIssue


@dataclass(frozen=True, slots=True)
class RevisionResult:
    chapter: int
    revised_text: str
    revision_log: list[str]
    issues_addressed: list[dict[str, Any]]


class ChapterReviser:
    def revise(
        self, chapter_number: int, chapter_text: str, issues: list[AuditIssue]
    ) -> RevisionResult:
        revision_log = [self._revision_note(issue) for issue in issues]
        issues_addressed = [self._issue_payload(issue) for issue in issues]

        if revision_log:
            revised_text = "\n".join([chapter_text, *revision_log])
        else:
            revised_text = chapter_text

        return RevisionResult(
            chapter=chapter_number,
            revised_text=revised_text,
            revision_log=revision_log,
            issues_addressed=issues_addressed,
        )

    def _revision_note(self, issue: AuditIssue) -> str:
        return f"<!-- REVISION NOTE: {issue.rule} - {issue.message} -->"

    def _issue_payload(self, issue: AuditIssue) -> dict[str, Any]:
        return {
            "rule": issue.rule,
            "severity": issue.severity,
            "message": issue.message,
            "location": dict(issue.location),
        }


__all__ = ["ChapterReviser", "RevisionResult"]
