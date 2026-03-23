# Findings: Make Chapter Revise Executable

> This file tracks research discoveries, decisions, and issues during planning and execution.
> **2-Action Rule**: After every 2 browser/view operations, save findings here.

## Requirements

- Add confidence router: AuditResult → RoutingDecision (pass/revise/rewrite/escalate)
- Add chapter reviser: chapter text + audit issues → revised text + revision log
- Expose `novel chapter route` and `novel chapter revise` CLI commands
- Both support `--json` for agent callers
- Template-based revision (no LLM)
- Output-only: no state mutation, no re-settle, no approve
- Prove continuation through `draft → settle → postcheck → audit → route → revise → snapshot`

## Research Findings

### Existing Pipeline Pattern

- Finding: All pipeline atoms follow the same pattern — runtime dataclass + runner class, CLI thin wrapper with `_emit`/`_fail`
- Source: `auditor.py`, `chapter.py`
- Implications: Router and reviser should follow identical structure

### Audit Contract (consumed by router)

- Finding: AuditResult fields: `chapter`, `status` (pass/fail), `severity` (none/minor/major/blocker), `recommended_action` (proceed_to_snapshot/revise_chapter), `issues` (list of AuditIssue)
- Source: `novel-runtime/novel_runtime/pipeline/auditor.py`
- Implications: Router maps `status` + `severity` to routing action; reviser consumes `issues` list

### Severity Order

- Finding: `_SEVERITY_ORDER = {"none": 0, "minor": 1, "major": 2, "blocker": 3}`
- Source: `auditor.py:8-13`
- Implications: Router can reuse this ordering for escalation thresholds

## Technical Decisions

| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| Router determinism | Pure severity-based rules, no LLM | Testable, fast, sufficient for pipeline shape proof | LLM-based routing (deferred) |
| Revision strategy | Template: append HTML comments | Matches drafter's template approach; proves pipeline shape | LLM spot-fix (deferred) |
| State mutation | Reviser is output-only | Settler owns state mutation exclusively | Reviser could re-settle (rejected: violates separation) |
| CLI composition | Revise invokes router internally | Simpler UX; route command exists separately for inspection | Require explicit route step before revise |
| Escalate/rewrite handling | CLI exits non-zero, does NOT invoke reviser | These actions need human/full-rewrite, not spot-fix | Attempt partial revision anyway (rejected) |

## Issues Encountered

| Issue | Status | Resolution |
|-------|--------|------------|
| (none yet) | — | — |

## Resources

- `architecture-novel-runtime-v1.md` lines 723-775: Phase 3 roadmap
- `changes/make-chapter-audit-executable/design.md`: pattern reference
- `novel-runtime/novel_runtime/pipeline/auditor.py`: audit contract
- `novel-cli/novel_cli/commands/chapter.py`: CLI pattern

## Baseline Lock

- Active plan notes for this task live in `E:\github\novel\changes\make-chapter-revise-executable\...`, not in the worktree continuation directory.
- Locked the current chapter CLI surface at `draft`, `settle`, `postcheck`, and `audit` while making `route` and `revise` explicitly absent.
- Locked the current executable continuation spine in e2e coverage as `project init -> entity add -> chapter draft -> settle -> postcheck -> snapshot create -> state show`, with no route/revise step added yet.
- Exact verification command: `export PYTHONPATH="E:/github/novel/novel-cli;E:/github/novel/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_chapter.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_e2e.py tests/test_auditor.py tests/test_drafter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py`
- Exact result: `40 passed`.

## Router Contract

- Finding: Added failing-first router contract tests in `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_router.py` to freeze the runtime router surface before any implementation exists.
- Mapping frozen in tests:
  - `status="pass"` → `action="pass"`
  - `status="fail"` + `severity="major"` → `action="revise"`
  - `status="fail"` + blocker severity with fewer than 3 blocker issues → `action="rewrite"`
  - `status="fail"` + 3 or more blocker issues → `action="escalate"`
- Structured decision contract frozen in tests: `RoutingDecision.action`, `RoutingDecision.reason`, and `RoutingDecision.audit_summary` with `chapter`, `status`, `severity`, `recommended_action`, `issue_count`, and `blocker_issue_count`.
- Exact failing-first verification command: `export PYTHONPATH="E:/github/novel/novel-cli;E:/github/novel/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_router.py`
- Exact failing test names:
  - `test_route_returns_pass_decision_for_passing_audit`
  - `test_route_returns_revise_decision_for_major_audit_failure`
  - `test_route_returns_rewrite_decision_for_blocker_failure_below_escalation_threshold`
  - `test_route_returns_escalate_decision_for_three_or_more_blocker_issues`
- Exact failing-first outcome: `4 failed` because `novel_runtime.pipeline.router` does not exist yet and the contract tests fail with the explicit module-required message.

## Reviser Contract

- Result fields frozen in failing-first tests: `chapter`, `revised_text`, `revision_log`, `issues_addressed`.
- Success-path contract: `ChapterReviser().revise(1, chapter_text, issues)` appends one output-only HTML note per audit issue using `<!-- REVISION NOTE: {rule} - {message} -->`, keeps the original chapter text intact ahead of the note block, and returns addressed issues as the frozen audit payload shape.
- Skip-path contract: an empty issue list returns the original text unchanged with empty `revision_log` and `issues_addressed`.
- Input fixture shape reused from `novel_runtime.pipeline.auditor.AuditIssue` so the reviser contract stays aligned with Task 1 audit semantics.
- Exact failing-first command: `export PYTHONPATH="E:/github/novel/novel-cli;E:/github/novel/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_reviser.py`
- Exact failing test names:
  - `test_revise_returns_structured_revision_result_for_audit_issues`
  - `test_revise_returns_original_text_when_no_revision_is_needed`
- Current failure mode: `ModuleNotFoundError: No module named 'novel_runtime.pipeline.reviser'`, which is the intended red state before Task 5 implementation.

## Worktree Repair

- Repair was needed because the active worktree was missing the fuller local package/test baseline already being verified from the root working copy, which made future router/reviser verification depend on invalid hybrid root+worktree imports.
- Synchronized byte-for-byte from root into `E:\github\novel-worktrees\make-chapter-revise-executable`:
  - `novel-cli/novel_cli/**` from `E:\github\novel\novel-cli\novel_cli\`
  - `novel-runtime/novel_runtime/**` from `E:\github\novel\novel-runtime\novel_runtime\`
  - `tests/test_auditor.py`, `tests/test_settler.py`, `tests/test_postcheck.py`, `tests/test_cli_state_snapshot.py` from `E:\github\novel\tests\`
- Removed transient worktree-only artifacts after sync: `.pytest_cache`, `.claude/tdd-guard`, and all copied `__pycache__` directories under the worktree.
- Byte-for-byte verification outcome: `byte-for-byte sync verified` for both package trees and the four synced regression tests.
- Exact worktree-only green verification command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_chapter.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_e2e.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_drafter.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_auditor.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_settler.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_postcheck.py E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_cli_state_snapshot.py`
- Green verification outcome: `40 passed in 1.06s`.
- Exact worktree-only router red command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_router.py`
- Router red outcome: `4 failed` with `ModuleNotFoundError: No module named 'novel_runtime.pipeline.router'`, which remains the intended failing-first state.
- Exact worktree-only reviser red command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest E:/github/novel-worktrees/make-chapter-revise-executable/tests/test_reviser.py`
- Reviser red outcome: `2 failed` with `ModuleNotFoundError: No module named 'novel_runtime.pipeline.reviser'`, which remains the intended failing-first state.
- Diagnostics after repair: `lsp_diagnostics` reported 0 issues across synced worktree `novel_cli`, `novel_runtime`, and `tests` Python files.
- Import-resolution proof with worktree-only `PYTHONPATH`: `novel_cli.__file__ -> E:\github\novel-worktrees\make-chapter-revise-executable\novel-cli\novel_cli\__init__.py`, `novel_runtime.__file__ -> E:\github\novel-worktrees\make-chapter-revise-executable\novel-runtime\novel_runtime\__init__.py`.

## Router Implementation

- Added `E:\github\novel-worktrees\make-chapter-revise-executable\novel-runtime\novel_runtime\pipeline\router.py` as a pure runtime module with frozen dataclass `RoutingDecision(action, reason, audit_summary)` and `ChapterRouter.route(audit)`.
- Routing rules implemented exactly against the frozen contract:
  - `audit.status == "pass"` always returns `action="pass"` with reason `audit passed with no blocking issues`, regardless of severity.
  - `audit.status == "fail"` and `audit.severity == "blocker"` returns `rewrite` when blocker issue count is below 3.
  - `audit.status == "fail"` and `audit.severity == "blocker"` returns `escalate` when blocker issue count is 3 or more.
  - All other failing severities route to `revise` with stable reason `audit failed with {severity} severity`.
- `audit_summary` is intentionally structured for downstream CLI/runtime consumers and includes only the frozen fields: `chapter`, `status`, `severity`, `recommended_action`, `issue_count`, and `blocker_issue_count`.
- Blocker escalation counts only issues whose own `issue.severity` is `blocker`; the router does not mutate `AuditResult`, touch the filesystem, or rely on LLM behavior.
- Used a relative import (`from .auditor import AuditResult`) so the worktree package resolves cleanly under `lsp_diagnostics`.

## Reviser Implementation

- Implemented `novel_runtime.pipeline.reviser` as a deterministic, output-only runtime module with `RevisionResult` frozen to `chapter`, `revised_text`, `revision_log`, and `issues_addressed`.
- The revision note template is locked exactly to `<!-- REVISION NOTE: {rule} - {message} -->` and is emitted once per audit issue in input order.
- Reviser behavior is append-only: when issues exist it preserves the original chapter text and appends note lines separated by newlines; when no issues exist it returns the original text unchanged.
- Addressed issues are returned in the frozen audit payload shape (`rule`, `severity`, `message`, `location`) using copied dictionaries so the reviser does not mutate incoming issue objects or any canonical state.
- Module style matches the existing pipeline pattern: slotted frozen dataclass result, thin runner class, relative sibling import, and explicit `__all__` export.

## CLI Route Command

- Added `novel chapter route --chapter N --audit-file PATH [--json]` to the worktree CLI chapter group only; `revise` remains absent from the help surface.
- The command follows the existing thin-CLI pattern from `audit`/`postcheck`: load project state, verify the requested chapter exists, decode the audit file through `_load_json_object`, hydrate runtime `AuditResult`/`AuditIssue`, invoke `ChapterRouter`, format, and `_emit`.
- Invalid audit input now fails through existing CLI helpers in two layers: malformed JSON or non-object payloads fail via `_load_json_object`, and object payloads missing the frozen audit contract fail with `invalid audit file JSON: expected audit result object`.
- Plain text output is intentionally minimal and human-readable: `Chapter`, `Action`, and `Reason`; JSON output mirrors the runtime routing contract with `action`, `reason`, and `audit_summary`.
- Exit-code semantics are now explicit at the CLI edge: `pass` and `revise` exit 0, while `rewrite` and `escalate` emit their payload and then exit 1.
- Focused verification command: `export PYTHONPATH="E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime" && rtk python -m pytest tests/test_cli_chapter.py -k route`
- Focused verification outcome: `5 passed, 10 deselected`.

## CLI Revise Command

- Added `novel chapter revise --chapter N --text-file PATH --audit-file PATH [--json]` to the worktree chapter CLI while leaving approve/export/startup behavior and e2e continuation untouched.
- The command stays thin like `route`: load state, validate the chapter exists, read chapter text with `_read_text_file`, hydrate the audit via `_load_audit_result`, route through `ChapterRouter`, then branch at the CLI edge.
- `pass` returns exit 0 with a no-revision-needed payload/message and does not create `chapters/chapter_N_revised.md`.
- `rewrite` and `escalate` reuse the existing route-format payload, emit the routing decision, return exit 1, and skip all file writes.
- Only `action="revise"` invokes `ChapterReviser`, writes `chapters/chapter_N_revised.md`, and emits JSON containing `revised_text`, `revision_log`, `issues_addressed`, and `routing_action` plus the output path.
- Focused Task 7 verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_cli_chapter.py -k revise`
- Focused Task 7 verification outcome: `5 passed, 14 deselected`.
- Diagnostics outcome: `lsp_diagnostics` returned no diagnostics for `novel_cli/commands/chapter.py` and `tests/test_cli_chapter.py` after the revise changes.

## Output-Only Guardrails

- Added runtime guardrails in `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_reviser.py` that freeze `ChapterReviser.revise(self, chapter_number, chapter_text, issues)` as an output-only contract; the assertion message explicitly records that settle/postcheck/approve/LLM remain deferred downstream steps.
- Added a reviser payload-copy test proving `issues_addressed` is detached from later mutation of the incoming `AuditIssue.location`, which keeps revise bounded to returned output data instead of mutating upstream inputs.
- Added CLI guardrail coverage in `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_chapter.py` that snapshots canonical state before/after `chapter revise`, monkeypatches `ChapterSettler`, `PostcheckRunner`, and `CanonicalState.save` to fail if touched, and confirms the revise path exits 0 without invoking any of them.
- File-side-effect proof is frozen by asserting the revise action adds exactly one new project file, `chapters/chapter_6_revised.md`; the diff assertion and explicit `approve`/`export` negative checks document that no downstream approve/export artifacts are introduced.
- Added a pass-path guardrail asserting `chapter revise` with a pass audit leaves both canonical state and the full project file set unchanged, preserving the Task 7 contract of exit 0 / no write for pass.
- Task 8 verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_reviser.py tests/test_cli_chapter.py -k "revise and not route"`
- Task 8 verification outcome: `10 passed, 15 deselected`.
- Diagnostics outcome: `lsp_diagnostics` returned no diagnostics for `tests/test_reviser.py` and `tests/test_cli_chapter.py` after the guardrail additions.

## E2E Continuation

- Extended only `E:\github\novel-worktrees\make-chapter-revise-executable\tests\test_cli_e2e.py` so both lifecycle tests now execute the full non-interactive continuation spine `draft -> settle -> postcheck -> audit -> route -> revise -> snapshot`.
- The e2e flow now captures structured `audit` JSON, writes that payload to `audit.json`, and feeds the same CLI-produced artifact into `chapter route` and `chapter revise` instead of fabricating a separate downstream fixture.
- Route assertions are locked to the pass decision payload (`action`, `reason`, `audit_summary`) and revise assertions are locked to the pass/no-write payload (`chapter`, `routing_action`, `reason`) so the continuation proof stays JSON-first where the CLI exposes structured output.
- The revise step is intentionally exercised on a passing audit to preserve Task 8 output-only guardrails inside e2e coverage: the spine reaches revise, no `chapter_1_revised.md` is created, canonical settled state remains unchanged, and snapshot still captures the post-settle/post-audit state.
- Task 9 verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_cli_e2e.py -k chapter`
- Task 9 verification outcome: `2 passed in 0.37s`.

## Task 10 Verification Evidence

- Used the explicit worktree-only `PYTHONPATH` for both Task 10 commands so imports resolved from `E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli` and `.../novel-runtime`.
- Exact targeted verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_router.py tests/test_reviser.py tests/test_cli_chapter.py tests/test_cli_e2e.py -k "route or revise"`
- Exact targeted verification outcome: `19 passed, 12 deselected in 0.55s`.
- Exact broader impacted verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_router.py tests/test_reviser.py tests/test_auditor.py tests/test_cli_chapter.py tests/test_cli_e2e.py tests/test_drafter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py`
- Exact broader impacted verification outcome: `59 passed in 1.12s`.
- Task 10 completed as verification-only: no code fixes were required and no worktree code files changed during this pass.

## Final Review Blockers — Route/Revise CLI Slice

- `chapter route` and `chapter revise` both accepted audit JSON for the wrong chapter because `_load_audit_result()` only validated payload shape; the CLI now performs an explicit `audit.chapter == --chapter` check immediately after loading and rejects mismatches through the existing `_raise_fail` helper path.
- The new invalid-input message is locked to `audit file chapter '{audit.chapter}' does not match --chapter '{chapter_number}'`, which preserves the established plain/JSON error envelope semantics without introducing a new failure pattern.
- `chapter revise` JSON output remains unchanged; only the plain success formatter changed from a path-only line to a real summary with `Chapter`, `Action`, `Issues addressed`, and `Output path`.
- Focused regression coverage added for both mismatch blockers plus the plain revise summary contract.
- Final focused verification command: `export PYTHONPATH='E:/github/novel-worktrees/make-chapter-revise-executable/novel-cli;E:/github/novel-worktrees/make-chapter-revise-executable/novel-runtime' && rtk python -m pytest tests/test_cli_chapter.py -k "route or revise"`
- Final focused verification outcome: `13 passed, 10 deselected in 0.55s`.
- Diagnostics outcome after the blocker fix: `lsp_diagnostics` returned no diagnostics for `novel_cli/commands/chapter.py` and `tests/test_cli_chapter.py`.
