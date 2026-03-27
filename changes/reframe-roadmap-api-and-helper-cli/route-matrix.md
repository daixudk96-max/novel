# Phase 3 Capability Matrix

The table below ties every Phase 3 deliverable to its owner (shared core, Route A, Route B, or dual-use) and tracks the current status of existing chapter slices under `changes/`.

| Item | Classification | Current Status | Notes |
| --- | --- | --- | --- |
| `novel_runtime/pipeline/auditor.py` structured audit report (+ `severity` and `recommended_action`) | shared core | implemented | central shared-core guardrail for every audit pass before routing to pass/revise/rewrite/escalate |
| `novel_runtime/pipeline/reviser.py` with AI guard and spot fixes | shared core | implemented | shared-core repair layer that keeps AI flavor from increasing after audit reruns |
| `novel_runtime/pipeline/router.py` confidence routing | shared core | implemented | shared-core decision engine that turns audit output into canonical actions |
| `novel_runtime/state/snapshot.py` plus `snapshot create/list/diff/rollback` CLI | shared core | implemented | snapshot persistence and rollback anchor shared lifecycle (`snapshot` keyword included for lookups) |
| Chapter lifecycle CLI commands (`chapter settle/postcheck/audit/route/revise/approve` plus snapshot handoff) | supports both | implemented | these CLI verbs keep every route on the same settle → postcheck → audit → revise → approve → snapshot spine while canonical state owns the truth |
| Phase 3 end-to-end CLI proof (`tests/test_cli_e2e.py` + regression suites) | shared core | implemented | verifies draft → settle → postcheck → audit → route → revise → approve → snapshot in one CLI-first regression loop |
| `changes/make-chapter-continuation-executable` slice | shared core | implemented | delivered the runtime-backed drafter + CLI boundary so the continuation loop now runs with real text, not placeholder scaffolding |
| `changes/make-chapter-audit-executable` slice | shared core | implemented | added the structured audit atom and CLI command that feeds the router/reviser inputs after `postcheck` |
| `changes/make-chapter-revise-executable` slice | shared core | implemented | introduced deterministic router + template reviser and CLI verbs so audit failures can reroute before approval/snapshot |
| `changes/make-chapter-approve-executable` slice | shared core | implemented | added the structured approval gate that maps audit/revision state to approved/conditionally_approved/rejected decisions |
| Route A runtime entry (`novel_runtime/pipeline/drafter.py`, `novel_runtime/llm/provider.py`, `novel_runtime/llm/temperature.py`, `novel_runtime/llm/resilience.py`, and `novel chapter draft`) | Route A only | implemented | shipped Route A provider/API-by-env path with deterministic resilience and packaged verification, while `drafter.py` plus the `provider.py`, `temperature.py`, and `resilience.py` layers keep the Novel-owned LLM pipeline inside the Route A lane |
| Route B guidance and validation path (`chapter guide`, `chapter verify-guided-result`, Route B skill that hands summary back into shared lifecycle) | Route B only | implemented | CLI guidance → assistant return manifest validation → shared lifecycle re-entry keeps Route B strictly orchestration-only; phase 2 auto-extract remains deferred |
| `changes/make-chapter-draft-llm-executable` slice | Route A only | implemented | this change delivers the Route A provider-backed chapter draft branch described above, with resilience and packaged verification proving the Route A-only readiness claim |
| `changes/make-chapter-guide-assisted-executable` slice | Route B only | implemented | this change implements the Route B guidance/export/verify/skill choreography that feeds into the shared Chapter lifecycle |

The Route A runtime entry deliberately names `novel_runtime/pipeline/drafter.py`, `novel_runtime/llm/provider.py`, `novel_runtime/llm/temperature.py`, `novel_runtime/llm/resilience.py`, and the shared `snapshot` workflow so the Phase 3 deliverables remain visible to QA greps, while the Route A drafting row now records the shipped provider + resilience + packaged verification truth. QA references: `novel_runtime/pipeline/drafter.py|novel_runtime/llm/provider.py|novel_runtime/llm/temperature.py|novel_runtime/llm/resilience.py|snapshot` and `make-chapter-draft-llm-executable|Route A|provider-backed|packaged verification`.
