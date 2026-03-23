from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .auditor import AuditResult


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    action: str
    reason: str
    audit_summary: dict[str, Any]


class ChapterRouter:
    def route(self, audit: AuditResult) -> RoutingDecision:
        audit_summary = self._audit_summary(audit)

        if audit.status == "pass":
            return RoutingDecision(
                action="pass",
                reason="audit passed with no blocking issues",
                audit_summary=audit_summary,
            )

        if audit.severity == "blocker":
            blocker_issue_count = audit_summary["blocker_issue_count"]
            if blocker_issue_count >= 3:
                return RoutingDecision(
                    action="escalate",
                    reason=(
                        f"audit failed with {blocker_issue_count} blocker issues and requires escalation"
                    ),
                    audit_summary=audit_summary,
                )
            return RoutingDecision(
                action="rewrite",
                reason=(
                    f"audit failed with blocker severity across {blocker_issue_count} blocker issues"
                ),
                audit_summary=audit_summary,
            )

        return RoutingDecision(
            action="revise",
            reason=f"audit failed with {audit.severity} severity",
            audit_summary=audit_summary,
        )

    def _audit_summary(self, audit: AuditResult) -> dict[str, Any]:
        blocker_issue_count = sum(
            1 for issue in audit.issues if issue.severity == "blocker"
        )
        return {
            "chapter": audit.chapter,
            "status": audit.status,
            "severity": audit.severity,
            "recommended_action": audit.recommended_action,
            "issue_count": len(audit.issues),
            "blocker_issue_count": blocker_issue_count,
        }


__all__ = ["RoutingDecision", "ChapterRouter"]
