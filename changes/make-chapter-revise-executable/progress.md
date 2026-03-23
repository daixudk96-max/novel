# Progress: Make Chapter Revise Executable

> This file tracks execution progress, test results, and errors.
> Update after completing each task or encountering issues.

## Session Log

### 2026-03-22 Session 0 — Planning

**Focus**: Create change directory and planning documents
**Status**: Completed

#### Actions Taken
- [x] Created `changes/make-chapter-revise-executable/` directory
- [x] Wrote `proposal.md` — problem statement, solution, risks, alternatives
- [x] Wrote `design.md` — architecture, file changes, key decisions, edge cases
- [x] Wrote `tasks.md` — 10 tasks across 4 phases
- [x] Wrote `findings.md` — requirements, research, technical decisions
- [x] Wrote `progress.md` — this file

#### Files Created
- `changes/make-chapter-revise-executable/proposal.md` (created)
- `changes/make-chapter-revise-executable/design.md` (created)
- `changes/make-chapter-revise-executable/tasks.md` (created)
- `changes/make-chapter-revise-executable/findings.md` (created)
- `changes/make-chapter-revise-executable/progress.md` (created)

#### Phase Progress
- Phase 0 (Scope lock): ⏳ Pending (0/3 tasks)
- Phase 1 (Runtime MVP): ⏳ Pending (0/2 tasks)
- Phase 2 (CLI surface): ⏳ Pending (0/3 tasks)
- Phase 3 (Verification): ⏳ Pending (0/2 tasks)

---

## Test Results

| Test Suite | Pass | Fail | Skip | Notes |
|------------|------|------|------|-------|
| (not yet run) | — | — | — | — |

## Error Log

| Timestamp | Error | Attempt | Context | Resolution |
|-----------|-------|---------|---------|------------|
| (none yet) | — | — | — | — |

## 5-Question Reboot Check

| Question | Answer |
|----------|--------|
| 1. What phase/task am I on? | Phase 0, Task 1 (not yet started) |
| 2. What was I doing when I stopped? | Finished planning, ready for execution |
| 3. What's the next action? | Lock baseline: run existing test suite and record pass count |
| 4. Are there any blockers? | No |
| 5. What files are currently modified? | Only new planning docs in changes/ |

## 2026-03-23 Task 1 — Baseline Lock

- Completed Task 1 by tightening only `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_chapter.py` and `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_e2e.py`.
- Active plan notes for this task live in `E:\github\novel\changes\make-chapter-revise-executable\...`, not in the worktree continuation directory.
- Locked the current executable chapter surface to `draft`, `settle`, `postcheck`, and `audit`; `route` and `revise` remain explicitly absent from the help surface and lifecycle coverage.
- Verification command: `export PYTHONPATH="E:/github/novel/novel-cli;E:/github/novel/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_chapter.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_e2e.py tests/test_auditor.py tests/test_drafter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py`
- Verification outcome: `40 passed`.

## 2026-03-23 Task 2 — Freeze Router Contract in Failing-First Tests

- Status: Completed (test-only contract freeze; router implementation intentionally absent)
- Modified file: `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_router.py`
- Added four failing-first contract tests covering routing paths `pass`, `revise`, `rewrite`, and `escalate`.
- Structured contract frozen on `RoutingDecision.action`, `RoutingDecision.reason`, and `RoutingDecision.audit_summary`.
- Verification command: `export PYTHONPATH="E:/github/novel/novel-cli;E:/github/novel/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_router.py`
- Verification outcome: `4 failed` with missing `novel_runtime.pipeline.router`, which is the expected failing-first state.
- Failing-first test count: `4`
- Failing tests:
  - `test_route_returns_pass_decision_for_passing_audit`
  - `test_route_returns_revise_decision_for_major_audit_failure`
  - `test_route_returns_rewrite_decision_for_blocker_failure_below_escalation_threshold`
  - `test_route_returns_escalate_decision_for_three_or_more_blocker_issues`

## 2026-03-23 Task 3 — Reviser Contract Tests

- Status: Completed (failing-first tests only; no reviser implementation added).
- Design sketch:
  1. Add only `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_reviser.py`.
  2. Freeze two runtime paths: revision applied for audit issues and skip when no revision is needed.
  3. Reuse `novel_runtime.pipeline.auditor.AuditIssue` payload semantics and require `chapter`, `revised_text`, `revision_log`, and `issues_addressed` on `RevisionResult`.
  4. Freeze the output-only note template as `<!-- REVISION NOTE: {rule} - {message} -->`.
- Verification command: `export PYTHONPATH="E:/github/novel/novel-cli;E:/github/novel/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_reviser.py`
- Verification outcome: `2 failed`.
- Failing-first test count: `2`.
- Exact failing tests:
  - `test_revise_returns_structured_revision_result_for_audit_issues`
  - `test_revise_returns_original_text_when_no_revision_is_needed`
- Failure detail: `ModuleNotFoundError: No module named 'novel_runtime.pipeline.reviser'` surfaced through the contract loader helper, confirming the intended red state.

## 2026-03-23 Worktree Repair

- Status: Completed.
- Why: the active worktree lacked the self-contained package/test baseline and was relying on an invalid hybrid root+worktree import path for future router/reviser work.
- Synced from root into `E:\github\novel-worktrees\make-chapter-revise-executable`:
  - `novel-cli/novel_cli/**`
  - `novel-runtime/novel_runtime/**`
  - `tests/test_auditor.py`
  - `tests/test_settler.py`
  - `tests/test_postcheck.py`
  - `tests/test_cli_state_snapshot.py`
- Removed worktree-only transient artifacts: `.pytest_cache`, `.claude/tdd-guard`, and all `__pycache__` directories under the worktree.
- Byte-for-byte verification: `byte-for-byte sync verified`.
- Green verification command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_chapter.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_e2e.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_drafter.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_auditor.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_settler.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_postcheck.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_state_snapshot.py`
- Green verification outcome: `40 passed in 1.06s`.
- Router red command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_router.py`
- Router red outcome: `4 failed` with missing `novel_runtime.pipeline.router`.
- Reviser red command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_reviser.py`
- Reviser red outcome: `2 failed` with missing `novel_runtime.pipeline.reviser`.
- Diagnostics: `lsp_diagnostics` returned 0 issues for synced worktree Python files.
- Import-resolution proof: `novel_cli.__file__` and `novel_runtime.__file__` both resolved from `E:\github\novel-worktrees\make-chapter-revise-executable\...`, not the root package trees.

## 2026-03-23 Task 4 — Runtime Confidence Router Module

- Status: Completed.
- Modified file: `E:\github\novel-worktrees\make-chapter-revise-executable\novel-runtime\novel_runtime\pipeline\router.py`
- Added pure deterministic runtime routing with `RoutingDecision(action, reason, audit_summary)` and `ChapterRouter.route(audit)`.
- Implemented frozen routing paths: pass for audit pass, revise for non-blocker failures, rewrite for blocker failures below 3 blocker issues, and escalate for blocker failures at 3 or more blocker issues.
- `audit_summary` now returns the frozen contract payload: `chapter`, `status`, `severity`, `recommended_action`, `issue_count`, and `blocker_issue_count`.
- Diagnostics outcome: `lsp_diagnostics` returned 0 issues for `router.py` and `tests/test_router.py`.
- Verification command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_router.py`
- Verification outcome: `4 passed in 0.09s`.

## 2026-03-23 Task 5 — Runtime Chapter Reviser

- Status: Completed.
- Modified file: `E:\github\novel-worktrees\make-chapter-revise-executable\novel-runtime\novel_runtime\pipeline\reviser.py`
- Added deterministic template-based reviser output that preserves the original chapter text and appends `<!-- REVISION NOTE: {rule} - {message} -->` once per audit issue.
- Frozen result contract implemented on `RevisionResult.chapter`, `RevisionResult.revised_text`, `RevisionResult.revision_log`, and `RevisionResult.issues_addressed`.
- Edge-case handling: empty issue lists return the original text unchanged with empty logs, and issue payloads are copied into dict form so no state or input object mutation occurs.
- Verification command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_reviser.py`
- Verification outcome: `2 passed in 0.09s`.

## 2026-03-23 Task 6 — CLI Route Command

- Status: Completed.
- Modified files:
  - `E:\github\novel-worktrees\make-chapter-revise-executable\novel-cli\novel_cli\commands\chapter.py`
  - `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_chapter.py`
- Design sketch:
  1. Extend only the chapter CLI surface with `route`; keep `revise` absent.
  2. Match the existing `postcheck`/`audit` flow: load state, validate chapter existence, read audit JSON, invoke runtime router, format, emit, then gate exit code on routing action.
  3. Add focused tests for help exposure, plain text success, JSON success, invalid audit payloads, and non-zero `rewrite`/`escalate` exits.
- Implementation outcome: `route` now accepts `--chapter`, `--audit-file`, and `--json`, hydrates runtime `AuditResult` from the audit file, and emits plain text or JSON without touching unrelated chapter commands.
- Exit semantics: `pass` and `revise` return exit code 0; `rewrite` and `escalate` return exit code 1 after emitting their payload.
- Diagnostics outcome: `lsp_diagnostics` returned 0 issues for `novel_cli/commands/chapter.py` and `tests/test_cli_chapter.py`.
- Verification command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest tests/test_cli_chapter.py -k route`
- Verification outcome: `5 passed, 10 deselected`.

## 2026-03-23 Task 7 — CLI Revise Command

- Status: Completed.
- Modified files:
  - `E:\github\novel-worktrees\make-chapter-revise-executable\novel-cli\novel_cli\commands\chapter.py`
  - `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_chapter.py`
- Design sketch:
  1. Extend only the chapter CLI surface with `revise`, keeping the command thin and reusing the existing chapter helpers.
  2. Route the hydrated audit first, then only call `ChapterReviser` and write `chapters/chapter_N_revised.md` when the router returns `revise`.
  3. Cover help exposure, revise success (plain and JSON), pass/no-write exit 0, and rewrite/escalate non-zero/no-write in focused CLI tests.
- Implementation outcome: `revise` now accepts `--chapter`, `--text-file`, `--audit-file`, and `--json`, validates the chapter exists in state, reads the text/audit inputs, routes internally, and only writes revised output for the `revise` action.
- Output semantics: `pass` emits a no-revision-needed result and exits 0; `rewrite` and `escalate` emit the routing decision and exit 1 without writing any revised file; `revise` emits the revision payload including `revised_text`, `revision_log`, `issues_addressed`, and `routing_action`.
- Diagnostics outcome: `lsp_diagnostics` returned 0 issues for `novel_cli/commands/chapter.py` and `tests/test_cli_chapter.py`.
- Verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_cli_chapter.py -k revise`
- Verification outcome: `5 passed, 14 deselected`.

## 2026-03-23 Task 8 — Keep Reviser Output-Only and Defer Downstream Steps

- Status: Completed.
- Modified files:
  - `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_reviser.py`
  - `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_chapter.py`
- Design sketch:
  1. Add only guardrail tests; keep production CLI/runtime behavior unchanged.
  2. Freeze the reviser contract as output-only by locking its input signature and copied issue payload semantics.
  3. Prove at the CLI layer that `chapter revise` does not mutate canonical state, does not save state, does not invoke settle/postcheck, and does not introduce approve/export side-effect files.
- Implementation outcome: added reviser-level contract tests plus CLI guardrail tests that compare canonical state and project file inventories before/after revise while monkeypatching `ChapterSettler`, `PostcheckRunner`, and `CanonicalState.save` to fail if the revise path touches deferred downstream behavior.
- Preserved Task 7 contract: pass still exits 0 with no write, revise still writes only the revised file, and rewrite/escalate still exit 1 with no revised-file write.
- Diagnostics outcome: `lsp_diagnostics` returned 0 issues for `tests/test_reviser.py` and `tests/test_cli_chapter.py`.
- Verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_reviser.py tests/test_cli_chapter.py -k "revise and not route"`
- Verification outcome: `10 passed, 15 deselected`.

## 2026-03-23 Task 9 — Extend the E2E Continuation Path

- Status: Completed.
- Modified file: `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_e2e.py`
- Design sketch:
  1. Extend only the existing lifecycle tests; keep all production CLI/runtime behavior unchanged.
  2. Run `chapter audit`, persist its CLI JSON output to `audit.json`, and feed that artifact into `chapter route` and `chapter revise` so the continuation remains CLI-first.
  3. Prefer structured assertions for audit/route/revise while preserving the settled-state and snapshot checks already frozen in the e2e coverage.
- Implementation outcome: both lifecycle tests now prove the continuation spine `draft -> settle -> postcheck -> audit -> route -> revise -> snapshot`, assert the pass-route JSON contract, and confirm the pass revise step stays output-only by not creating `chapter_1_revised.md` before snapshot.
- Diagnostics outcome: `lsp_diagnostics` returned 0 issues for `tests/test_cli_e2e.py`.
- Verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_cli_e2e.py -k chapter`
- Verification outcome: `2 passed in 0.37s`.

## 2026-03-23 Task 10 — Targeted and Impacted Verification

- Status: Completed.
- Files changed during this task:
  - `E:\github\novel\changes\make-chapter-revise-executable\findings.md`
  - `E:\github\novel\changes\make-chapter-revise-executable\progress.md`
- Design sketch:
  1. Run the exact targeted Task 10 route/revise suite with the explicit worktree `PYTHONPATH`.
  2. Run the exact broader impacted regression suite with the same `PYTHONPATH`.
  3. Append exact commands and exact outcomes to the append-only notes; do not touch code unless a minimal verification fix is required.
- Verification command 1: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_router.py tests/test_reviser.py tests/test_cli_chapter.py tests/test_cli_e2e.py -k "route or revise"`
- Verification outcome 1: `19 passed, 12 deselected in 0.55s`.
- Verification command 2: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_router.py tests/test_reviser.py tests/test_auditor.py tests/test_cli_chapter.py tests/test_cli_e2e.py tests/test_drafter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py`
- Verification outcome 2: `59 passed in 1.12s`.
- Follow-up: none; both Task 10 verification commands passed without requiring any code changes.

## 2026-03-23 Final Review Blocker Fix — Route/Revise CLI Slice

- Status: Completed.
- Modified files:
  - `E:\github\novel-worktrees\make-chapter-revise-executable\novel-cli\novel_cli\commands\chapter.py`
  - `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_chapter.py`
- Design sketch:
  1. Keep the fix inside the existing CLI slice only; do not touch runtime router/reviser modules.
  2. Reject audit files whose embedded `chapter` does not match `--chapter` by reusing the existing CLI invalid-input failure helper.
  3. Change only plain-text revise success output so it reports a real summary while leaving the JSON payload and output-only guardrails untouched.
- Implementation outcome: added a shared audit/chapter validation helper used by both `route` and `revise`, switched revise plain output to a summary formatter, and added focused regression assertions for route mismatch, revise mismatch, and plain revise summary content.
- Diagnostics outcome: `lsp_diagnostics` returned 0 issues for `novel_cli/commands/chapter.py` and `tests/test_cli_chapter.py`.
- Verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_cli_chapter.py -k "route or revise"`
- Verification outcome: `13 passed, 10 deselected in 0.55s`.
