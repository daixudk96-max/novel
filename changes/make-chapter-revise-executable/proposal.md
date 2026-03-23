# Proposal: Make Chapter Revise Executable

## Problem Statement

`make-chapter-audit-executable` delivered the audit atom and proved the continuation path through `draft -> settle -> postcheck -> audit -> snapshot`. But when audit finds issues, the pipeline has no automated way to decide what to do next (router) or to perform revision (reviser). The pipeline jumps from audit straight to snapshot, skipping the quality-improvement loop.

Per the architecture roadmap (Phase 3), the full target lifecycle is:
`draft → settle → postcheck → audit → revise → approve → snapshot`

The two missing atoms between audit and approve are the **confidence router** and the **chapter reviser**.

## Why This Next

- Roadmap order: router/revise is the next gap after audit in the Phase 3 continuation spine.
- Audit already emits `recommended_action` (`revise_chapter` / `proceed_to_snapshot`) — the router and reviser are the natural consumers of that contract.
- Approve depends on a stable revise output; doing approve first would be premature.
- LLM integration is a separate concern — this slice uses template-based revision (like the current drafter) to prove the pipeline shape first.

## Proposed Solution

Add two new runtime pipeline atoms and two new CLI commands:

1. **Confidence Router** (`novel chapter route`) — deterministic logic that maps an audit result to a routing decision: `pass`, `revise`, `rewrite`, or `escalate`.
2. **Chapter Reviser** (`novel chapter revise`) — template-based spot-fix engine that takes chapter text + audit issues and produces revised text with a revision log.

Both follow the established pattern: runtime owns logic, CLI is a thin wrapper, both support `--json` for agent callers.

## Success Criteria

- `novel chapter route` exists and returns structured routing decisions.
- `novel chapter revise` exists and returns revised chapter text.
- Router correctly maps audit severities to routing actions.
- Reviser produces modified text based on audit issues.
- The continuation flow can be proven through `draft → settle → postcheck → audit → route → revise → snapshot`.
- No approve, export, or startup behavior is added in this change.
- All existing tests continue to pass (48+ tests).

## Risk Assessment

### Risk 1: Scope expansion into approve/export/LLM

Router and reviser naturally tempt the plan to include approval gates and real LLM calls.

**Mitigation:** This change stops at template-based revision. Approve is explicitly deferred. LLM integration is a separate future slice.

### Risk 2: Reviser mutates canonical state

If the reviser writes back to state, it violates the settler's exclusive responsibility.

**Mitigation:** Reviser is output-only — it returns revised text but does NOT call settler or modify canonical state. Re-settling after revision is a future concern.

### Risk 3: Router logic becomes too complex

Over-engineering the routing decision tree before real LLM audit data exists.

**Mitigation:** Start with simple severity-based rules. The router is deterministic and testable. Complexity can be added when real audit data arrives.

### Risk 4: Duplicate logic with auditor

Reviser may re-implement issue detection instead of consuming audit output.

**Mitigation:** Reviser takes AuditResult as input — it consumes, not duplicates, audit findings.

## Alternatives Considered

### Alternative A — Skip router, go straight to revise

Rejected. The router is a small, testable atom that decouples "what to do" from "how to do it". Without it, the reviser would need to embed routing logic internally.

### Alternative B — Do revise + approve together

Rejected. Approve depends on stable revise output and would expand scope too far.

### Alternative C — Wait for LLM integration before revise

Rejected. The pipeline shape can be proven with template-based revision first. LLM integration is orthogonal.
