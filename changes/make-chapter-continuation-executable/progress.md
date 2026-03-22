# Progress: Make Chapter Continuation Executable

## Session Log

- 2026-03-22: Created follow-on execution plan after the completed `agent-callable-novel-cli` foundation step.
- 2026-03-22: Confirmed the next roadmap target should be continuation, not startup, based on roadmap priority and current Python repo readiness.
- 2026-03-22: Wrote proposal/design/tasks/findings/progress for a narrow chapter-draft MVP plan.

## Phase Progress

- Phase 0 — Scope lock: planned
- Phase 1 — Runtime draft MVP: planned
- Phase 2 — Continuation slice proof: planned
- Phase 3 — Verification and closeout: planned

## Actions Taken

- Read roadmap source: `architecture-novel-runtime-v1.md`
- Read current foundation outputs under `changes/agent-callable-novel-cli/`
- Read current continuation implementation cluster in CLI/runtime/tests
- Consulted exploration + Metis to validate plan sequencing
- Created new execution-plan change directory and planning docs

## Test Results

- Planning only in this session; no new implementation tests were run for this change yet.
- 2026-03-22: Locked continuation baseline with narrow regression updates in `tests/test_cli_chapter.py` and `tests/test_cli_e2e.py`.
- 2026-03-22: Added explicit baseline assertions that `chapter draft` is still placeholder-only in plain + JSON CLI coverage, while `chapter settle`/`chapter postcheck`/`snapshot` remain the real continuation spine.
- 2026-03-22: Preserved non-regression expectations that settle marks chapters settled without replacing summaries, postcheck stays deterministic, and snapshots capture the settled continuation state.
- 2026-03-22: Baseline command recorded for this task: `rtk python -m pytest tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py tests/test_cli_e2e.py`.
- 2026-03-22: Verification passed in the current Windows shell with repo-local import wiring: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py tests/test_cli_e2e.py`.
- 2026-03-22: Replaced the placeholder baseline draft assertions with failing-first MVP contract tests in `tests/test_cli_chapter.py`, `tests/test_cli_e2e.py`, and new `tests/test_drafter.py`.
- 2026-03-22: Draft contract now requires exact success fields (`chapter`, `title`, `status`, `summary`, `path`), exact draft file content, and deterministic empty-world failures for plain + JSON CLI modes.
- 2026-03-22: Targeted verification failed for the intended reasons with repo-local import wiring: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_chapter.py -k draft` still hits placeholder-only CLI behavior, and `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_drafter.py` fails because `novel_runtime.pipeline.drafter` does not exist yet.
- 2026-03-22: Failing-first draft test names locked for the next implementation step: `test_draft_creates_runtime_backed_file`, `test_draft_json_output_matches_runtime_contract`, `test_draft_requires_active_world_entity_plain_output`, `test_draft_requires_active_world_entity_json_output`, `test_draft_returns_structured_chapter_result`, `test_draft_requires_active_world_entity`.

## Error Log

- None

## 5-Question Reboot Check

| Question | Answer |
|---|---|
| 1. Current change? | `make-chapter-continuation-executable` |
| 2. Why this change next? | Continuation is P0 and already has the strongest Python CLI/runtime spine. |
| 3. Core MVP target? | Replace placeholder-only `chapter draft` with a real runtime-backed draft flow. |
| 4. What is explicitly deferred? | Startup/outline/approve, full audit/revise, import/export, host-specific work. |
| 5. First execution move? | Lock baseline tests, then write failing-first draft contract tests. |

## Runtime Draft MVP Execution

- 2026-03-22: Implemented `novel_runtime.pipeline.drafter` as the minimal runtime-owned chapter draft MVP and exported it from `novel_runtime.pipeline`.
- 2026-03-22: Verified the runtime boundary with repo-local import wiring: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_drafter.py` passed.
- 2026-03-22: Verified CLI wiring is still intentionally deferred: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_chapter.py -k draft` still fails against placeholder-only CLI behavior.
- 2026-03-22: Deferred work remains limited to CLI integration in `novel_cli.commands.chapter`; this task did not add file writing, CLI JSON mapping, or broader continuation logic outside the runtime draft boundary.

## CLI Draft Wiring Execution

- 2026-03-22: Refactored `novel_cli.commands.chapter:draft_chapter` to call `ChapterDrafter().draft(...)` instead of building deterministic placeholder content in the command body.
- 2026-03-22: The CLI now writes the runtime draft markdown artifact to `chapters/chapter_{n}.md`, updates canonical chapter fields from the runtime result, and preserves existing `chapter settle` / `chapter postcheck` behavior.
- 2026-03-22: Tightened `tests/test_cli_chapter.py` plain success coverage to the exact emitted line `Drafted chapter {n} at {path}` while keeping the frozen JSON payload and empty-world failure contract unchanged.
- 2026-03-22: Targeted RED->GREEN verification succeeded with repo-local import wiring: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_chapter.py -k draft` now passes after the CLI refactor.
- 2026-03-22: Added test-only negative coverage in `tests/test_cli_chapter.py` for the draft missing-project prerequisite; the exact machine-checkable JSON failure is `{"error": "no novel project selected", "code": 1}` with exit code `1`.
- 2026-03-22: Added test-only runtime failure coverage in `tests/test_drafter.py` for invalid `chapter_number` type (`chapter_number must be an integer`) and blank-name active entities that still fail the active-world prerequisite (`chapter 2 draft requires at least one active world entity`).
- 2026-03-22: Verified the targeted failure-path slice with repo-local import wiring: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_chapter.py -k "draft or failure"` -> `5 passed, 3 deselected`; `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_drafter.py -k failure` -> `2 passed, 2 deselected`.
- 2026-03-22: Changed-file LSP diagnostics are clean for `tests/test_cli_chapter.py` and `tests/test_drafter.py`; remaining scope stays inside test coverage rather than widening draft/continuation implementation rules.

## E2E Continuation Coverage Execution

- 2026-03-22: Updated `tests/test_cli_e2e.py` only to replace the last placeholder-oriented lifecycle assumptions with real draft-path assertions.
- 2026-03-22: Plain-mode e2e coverage now asserts the exact emitted draft path and exact runtime-backed markdown artifact before the test authors the chapter text used for settle/postcheck.
- 2026-03-22: JSON-mode e2e coverage now asserts the resolved draft path plus the runtime-backed draft file body, then preserves the same carried summary through settled state and snapshot checks.
- 2026-03-22: Required repo-local verification command passed but selected no tests in this file: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_e2e.py -k chapter`.
- 2026-03-22: Executed full-file proof for the actual slice with repo-local import wiring: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_e2e.py` -> `2 passed`.
- 2026-03-22: Follow-up verification fix kept scope local to `tests/test_cli_e2e.py`: renamed the two lifecycle tests so the exact selector `-k chapter` now exercises the intended chapter lifecycle coverage.
- 2026-03-22: Exact required verification now passes with selected tests: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_e2e.py -k chapter` -> `2 passed`.

## Final Verification Wave

- 2026-03-22: Ran targeted continuation verification exactly as required: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_drafter.py tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_e2e.py -k chapter` -> pass (`13 passed, 14 deselected`).
- 2026-03-22: Ran full impacted regression suite exactly as required: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_drafter.py tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_e2e.py tests/test_cli_state_snapshot.py` -> pass (`32 passed`).
- 2026-03-22: This task remained verification-only; no code files under `novel-cli/`, `novel-runtime/`, or `tests/` were modified.

## Final-Wave Defect Fix

- 2026-03-22: Fixed the rejected final-wave state-consistency defect in `novel_cli.commands.chapter:_upsert_chapter()` by clearing stale `settled_at` when re-drafting an already settled chapter.
- 2026-03-22: Added a narrow regression test in `tests/test_cli_chapter.py` covering the settled -> draft redraft path and asserting the rewritten chapter record uses the draft contract with `settled_at == ""`.
- 2026-03-22: Scope stayed local to `chapter.py`, `tests/test_cli_chapter.py`, and append-only notes; runtime draft behavior and settle/postcheck implementations were unchanged.
- 2026-03-22: Final re-review verified the rejected path directly with repo-local import wiring: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_chapter.py -k settled_at` -> `1 passed`.
