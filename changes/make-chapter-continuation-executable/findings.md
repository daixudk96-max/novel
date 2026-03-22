# Findings: Make Chapter Continuation Executable

## Requirements

- Next roadmap step should target `章节续写流程`, not `新书启动流程`.
- The change must be a thin execution slice after the completed agent-callable contract step.
- Planning must stay CLI-first, runtime-owned, and TDD-driven.

## Research Findings

- Roadmap priority favors continuation first: `architecture-novel-runtime-v1.md` marks `章节续写流程` as P0 and `新书启动流程` as P1.
- Current continuation readiness is stronger than startup readiness in the Python stack.
- `novel-cli/novel_cli/commands/chapter.py` already exposes `draft`, `settle`, and `postcheck`, but `draft` is still placeholder-only.
- `novel-runtime/novel_runtime/pipeline/settler.py` and `postcheck.py` provide a real continuation spine that can be reused.
- Startup still lacks outline/approve atoms in the Python runtime/CLI, making it the broader greenfield target.

## Technical Decisions

- Chosen next change target: `make-chapter-continuation-executable`.
- Chosen MVP boundary: make `chapter draft` real first and prove the slice `draft -> settle -> postcheck -> snapshot`.
- Deferred for later changes unless absolutely required: startup/outline/approve, full audit/revise, import/export.

## Issues / Risks

- The biggest execution risk is accidentally growing this change into the full continuation epic.
- Existing e2e assertions currently encode placeholder-draft assumptions and will need to be rewritten carefully.

## Resources

- `architecture-novel-runtime-v1.md`
- `changes/agent-callable-novel-cli/design.md`
- `changes/agent-callable-novel-cli/capability-registry.md`
- `changes/agent-callable-novel-cli/workflow-spec.md`
- `novel-cli/novel_cli/commands/chapter.py`
- `novel-runtime/novel_runtime/pipeline/settler.py`
- `novel-runtime/novel_runtime/pipeline/postcheck.py`
- `tests/test_cli_chapter.py`
- `tests/test_cli_e2e.py`
- `tests/test_settler.py`
- `tests/test_postcheck.py`
- `tests/test_cli_state_snapshot.py`

## Baseline Lock Notes

- Baseline command to preserve for this scope-lock task: `rtk python -m pytest tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py tests/test_cli_e2e.py`.
- `chapter draft` is placeholder-only today in both plain and JSON CLI modes: it writes `# Chapter N` plus `This is a deterministic placeholder draft for chapter N.`, stores that same summary in canonical state, and leaves chapter status as `draft`.
- `chapter settle` is already part of the real continuation spine: it flips chapter status to `settled`, stamps `settled_at`, applies structured settlement updates, and does not replace an existing chapter summary on its own.
- `chapter postcheck` is already part of the real continuation spine: it returns deterministic pass/fail output derived from runtime checks rather than placeholder scaffolding.
- `snapshot create` is already part of the real continuation spine: in the lifecycle tests, the saved snapshot now explicitly captures the settled chapter/timeline state while the carried summary is still the placeholder draft summary.
- Added regression coverage in `tests/test_cli_chapter.py` and `tests/test_cli_e2e.py` to make the placeholder-vs-spine split explicit without treating the placeholder draft as the desired future MVP.

## Draft Contract Notes

- The failing-first draft MVP contract now expects runtime-backed draft prose derived from canonical state instead of the placeholder string: `Mira takes the next step.` / `Kai takes the next step.` in the targeted test fixtures.
- CLI success contract in `tests/test_cli_chapter.py` now freezes exact draft file content, exact chapter state update, and exact JSON payload fields: `chapter`, `title`, `status`, `summary`, `path`.
- CLI failure contract now freezes deterministic empty-world behavior: plain mode must emit `Error: chapter 1 draft requires at least one active world entity`, and JSON mode must emit `{"error": "chapter 1 draft requires at least one active world entity", "code": 1}`.
- Runtime contract in `tests/test_drafter.py` now expects a dedicated `novel_runtime.pipeline.drafter` module with `ChapterDrafter().draft(state, chapter_number)` returning structured result attributes `chapter`, `title`, `status`, `summary`, and `content`.
- Failing-first test names for this task: `test_draft_creates_runtime_backed_file`, `test_draft_json_output_matches_runtime_contract`, `test_draft_requires_active_world_entity_plain_output`, `test_draft_requires_active_world_entity_json_output`, `test_draft_returns_structured_chapter_result`, and `test_draft_requires_active_world_entity`.
- Current behavior does not satisfy the contract because `novel_cli.commands.chapter:draft_chapter` still writes placeholder-only content/payloads and never fails on an empty world model, while the runtime-owned drafter module does not exist yet.

## Runtime Draft MVP Notes

- Added `novel_runtime.pipeline.drafter` as the runtime-owned entrypoint for the draft MVP; it exposes `ChapterDrafter.draft(state, chapter_number)` and returns a frozen `ChapterDraft` result.
- The runtime-owned draft result now freezes the core fields `chapter`, `title`, `status`, `summary`, and `content`, leaving file writing and CLI output mapping deferred to later CLI wiring.
- Draft validation is deterministic and runtime-local: the drafter selects the first active world entity with a non-empty name and raises `chapter {n} draft requires at least one active world entity` when none exist.
- The MVP keeps state mutation out of the runtime draft path for now; this step only validates inputs and constructs deterministic output content from canonical state.

## CLI Runtime Wiring Notes

- `novel_cli.commands.chapter:draft_chapter` now treats the runtime drafter as the business-logic boundary: the CLI loads state, calls `ChapterDrafter().draft(...)`, writes `draft.content` to `chapters/chapter_{n}.md`, then persists canonical state.
- The CLI draft artifact is now the runtime-owned markdown body verbatim, so placeholder scaffolding is no longer generated in the command body.
- Canonical chapter updates now come from the runtime result fields (`chapter`, `title`, `status`, `summary`) while `settled_at` remains preserved/blank on draft records; `chapter settle` and `chapter postcheck` were left untouched.
- Draft JSON success payload now mirrors the frozen contract by emitting `chapter`, `title`, `status`, `summary`, and resolved `path`; plain success output was tightened in tests to the exact `Drafted chapter {n} at {path}` line.
- Empty-world draft failures now flow through the runtime validation message unchanged, preserving the exact frozen plain/json error behavior without adding new CLI-side wording.
- Current LSP workspace diagnostics still report unresolved `novel_runtime` / `novel_cli` imports in this repo layout even though repo-local `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime'` verification passes; no environment-wide tooling change was made in this task.

## Failure-Path Coverage Notes

- Added CLI draft failure coverage for the missing-project prerequisite in `tests/test_cli_chapter.py`: `--json chapter draft --chapter 1` must exit with code `1` and payload `{"error": "no novel project selected", "code": 1}`.
- Added runtime validation coverage for invalid inputs in `tests/test_drafter.py`: non-`int` `chapter_number` must raise `ValueError("chapter_number must be an integer")`.
- Added runtime validation coverage for malformed prerequisites in `tests/test_drafter.py`: active entities with blank names do not satisfy the draft prerequisite, so drafting chapter 2 still raises `ValueError("chapter 2 draft requires at least one active world entity")`.
- Current failure matrix now freezes three machine-checkable draft-side contracts inside the MVP boundary: missing selected project -> JSON `error`/`code`; missing usable active world entity -> exact draft failure message; invalid `chapter_number` type -> exact runtime validation message.
- Remaining MVP-boundary failures intentionally left as-is in this task: Click-level option parsing and non-draft continuation commands (`settle` / `postcheck`) were not broadened because this task was test-only and limited to draft/continuation handoff negatives.

## E2E Continuation Slice Notes

- `tests/test_cli_e2e.py` now proves the real draft path before continuation advances: it freezes the resolved chapter file path, exact runtime-backed markdown body `# Chapter 1\n\nKai takes the next step.\n`, and the emitted/plain JSON draft metadata.
- The remaining placeholder-only e2e assumptions were removed by renaming the captured draft artifact away from `placeholder_text` and by asserting the carried summary as the runtime-backed draft summary through settle/state/snapshot checks.
- The e2e continuation slice remains fully non-interactive: the test still replaces the drafted file with authored prose only through file writes inside the isolated filesystem, then runs settle, postcheck, and snapshot without prompts.
- The required verification command `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_cli_e2e.py -k chapter` currently deselects both lifecycle tests because neither test name contains `chapter`; full-file execution is still needed to exercise this slice until a later task changes selection semantics or test naming.
- Selector validity is fixed locally in `tests/test_cli_e2e.py` by renaming the two lifecycle tests to `test_chapter_full_lifecycle` and `test_chapter_full_lifecycle_json_mode`; this keeps behavior identical while making the plan's `-k chapter` filter meaningful.

## Final Verification Notes

- 2026-03-22: Targeted continuation verification passed with the exact required command: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_drafter.py tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_e2e.py -k chapter` -> `13 passed, 14 deselected`.
- 2026-03-22: Full impacted regression verification passed with the exact required command: `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime' rtk python -m pytest tests/test_drafter.py tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_e2e.py tests/test_cli_state_snapshot.py` -> `32 passed`.

## Final-Wave State Consistency Fix Notes

- Final-wave review surfaced one concrete defect in the completed CLI draft wiring: re-drafting an already settled chapter changed `status` back to `draft` but left a stale non-empty `settled_at` timestamp behind.
- The fix stayed local to `novel_cli.commands.chapter:_upsert_chapter()`: existing chapter records now clear `settled_at` to `""` whenever the draft path refreshes title/status/summary from the runtime draft result.
- The runtime/CLI boundary and payload contract remain unchanged: the CLI still consumes `ChapterDrafter().draft(...)`, writes the same artifact, and emits the same plain/json success and failure shapes.
- Added a narrow CLI regression in `tests/test_cli_chapter.py` proving that re-drafting a settled chapter rewrites the chapter record to the draft contract and resets `settled_at` to an empty string without changing settle/postcheck behavior.
- Re-review confirmation: the settled -> redraft reset is now covered end-to-end at the CLI layer (`draft_chapter` -> `_upsert_chapter` -> persisted canonical state), and the targeted selector `tests/test_cli_chapter.py -k settled_at` passes with repo-local `PYTHONPATH` wiring.
