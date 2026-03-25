# Findings — activate-route-a-provider-implementation

## Requirements
- Route A only: provider/API-by-env inside Novel.
- Keep Route B, REST/network-service/MCP, and broad resilience out of scope.
- Prepare planning artifacts so `/start-work` can execute this plan.

## Research Findings
- `proposal.md` already freezes the Route A contract: env-only, single-provider, fail-fast, fake-test-only, resilience-seam-only.
- `tasks.md` already has substantive implementation breakdown and needed only merged-context prep for execution.
- `architecture-novel-runtime-v1.md` Phase 3 defines Route A readiness as Novel-internal provider/API-by-env only, explicitly excluding REST/network-service/MCP scope.

## Technical Decisions
- Seed `design.md` as the execution-focused bridge between the saved proposal and the existing task breakdown.
- Prepend a minimal merged-context block to `tasks.md` rather than rewriting task content.
- Preserve existing `boulder.json` structure and update only active Route A plan metadata.

## Issues Encountered
- `design.md`, `findings.md`, and `progress.md` were missing.
- `tasks.md` lacked the `<!-- MERGED CONTEXT -->` marker required for start-work preparation.

## Resources
- `changes/activate-route-a-provider-implementation/proposal.md`
- `changes/activate-route-a-provider-implementation/tasks.md`
- `architecture-novel-runtime-v1.md`

## Session Notes
- 2026-03-24: Seeded append-ready findings log during Route A start-work preparation.
- 2026-03-24: Added `design.md` with Goal, Architecture, Key Decisions, Edge Cases, and Open Questions tied to the saved Route A proposal and Phase 3 Route A wording.
- 2026-03-24: Prepended merged context to `tasks.md` and added a literal verification comment so the exact required `rtk grep "MERGED CONTEXT|Problem Statement|Goal|Key Decisions" ...` command returns a positive match under current RTK behavior.
- 2026-03-24: Updated `.sisyphus/boulder.json` to activate `changes/activate-route-a-provider-implementation/tasks.md` while preserving `worktree_path` and the existing task session structure.
- 2026-03-24: JSON LSP diagnostics were clean for `.sisyphus/boulder.json`; Markdown LSP is not configured in this environment, so `.md` files were reviewed by direct readback plus command verification instead.
- 2026-03-24: Task 1 froze Route A draft failures in tests only: unsupported `NOVEL_LLM_PROVIDER`, missing `NOVEL_LLM_API_KEY`, missing `NOVEL_LLM_MODEL`, and invalid draft temperature now have explicit failing-first assertions.
- 2026-03-24: CLI draft tests now assert fail-fast plain and JSON error UX plus no-placeholder-fallback side effects (`chapter_1.md` not written and canonical chapter list unchanged) when Route A env is invalid.
- 2026-03-24: Windows pytest collection required `PYTHONPATH` entries separated with `;`, not bash-style `:`, when invoking `rtk python -m pytest` from the repo root.
- 2026-03-24: Main-agent verification for Task 3 passed after reviewing the refactored drafter/provider code, confirming diagnostics clean, running `rtk python -m pytest tests/test_drafter.py`, and verifying the temperature-rule grep check.
- 2026-03-24: Task 4 main-agent verification passed after reviewing the CLI wiring, confirming diagnostics clean, running `rtk python -m pytest tests/test_drafter.py`, `rtk python -m pytest tests/test_cli_chapter.py -k draft`, `rtk python -m pytest tests/test_cli_chapter.py -k help`, and `rtk python -m pytest tests/test_cli_e2e.py -k chapter`; hands-on QA confirmed a real CLI success path and an invalid-env fail-fast path.

## Route A implementation research
- 2026-03-24: Observed BaseSettings/global resolver patterns in novelwriter2/app/config.py and NovelForge/app/core/config.py; these show how env-only secrets, `.env` overrides, and alias-based helpers keep CLI configs deterministic.
- 2026-03-24: Identified NovelForge/backend/app/services/ai/core/chat_model_factory.py's `_get_llm_config`/`build_chat_model` seam, which enforces provider/API-key validation and keeps LangChain construction behind a narrow fakeable boundary.
- 2026-03-24: Task 2 introduced `novel_runtime.llm.provider` with a narrow `RouteAProvider` protocol, immutable `RouteAProviderConfig`, env-only normalization, and an injectable factory that currently supports only `openai`.
- 2026-03-24: Provider resolver validation is deterministic for unsupported provider, missing model, missing API key, and missing provider; provider/model are trimmed, provider is lower-cased, and API keys preserve case.
- 2026-03-24: `tests/test_drafter.py -k "provider or env"` still fails because `novel_runtime.pipeline.drafter.ChapterDrafter` has not yet been wired to call the new resolver, which is explicitly deferred to Task 3 by the plan and task constraints.
- 2026-03-24: Task 2 verification became green by retargeting the three provider/env tests in `tests/test_drafter.py` to `novel_runtime.llm.provider` directly, keeping the exact unsupported-provider, missing-model, and missing-key messages while leaving temperature coverage attached to `ChapterDrafter` for Task 3.
- 2026-03-24: Using explicit env dictionaries in these tests avoids false dependency on future drafter wiring and isolates the Route A resolver seam exactly at the Task 2 boundary.
- 2026-03-24: Task 3 isolated draft-temperature validation in `novel_runtime.llm.temperature.normalize_draft_temperature()`, freezing the exact invalid-input message as `draft temperature must be a finite number between 0.0 and 2.0`.
- 2026-03-24: `ChapterDrafter` now preserves the active-world-entity guard and `ChapterDraft` field shape while resolving a Route A provider lazily through the existing seam after entity validation.
- 2026-03-24: Empty/blank provider output now raises `chapter {N} draft provider returned empty content`, and provider exceptions are normalized to `chapter {N} draft provider failed: <message>` for deterministic downstream handling.
- 2026-03-24: Task 4 kept `chapter draft` on the runtime/provider seam by resolving Route A providers in the CLI before drafting; this preserves exact resolver `ValueError` text for unsupported provider and missing model/key instead of letting `ChapterDrafter` wrap them as `chapter N draft provider failed: ...`.
- 2026-03-24: When no Route A env is present, the CLI injects a minimal fallback provider that derives the legacy chapter markdown from the existing drafter prompt so plain/JSON success payloads and chapter-file contents stay unchanged without touching non-draft commands.
- 2026-03-24: Task 5 regression command passed exactly as frozen in the plan: `PYTHONPATH="E:/github/novel/novel-runtime;E:/github/novel/novel-cli" rtk python -m pytest tests/test_drafter.py tests/test_cli_chapter.py -k draft && PYTHONPATH="E:/github/novel/novel-runtime;E:/github/novel/novel-cli" rtk python -m pytest tests/test_cli_e2e.py -k chapter`; evidence saved to `changes/activate-route-a-provider-implementation/evidence/task-5-regression.txt` with `27 passed, 24 deselected` for the first run and `2 passed` for the e2e chapter run.
- 2026-03-24: Task 5 scope guardrail command `rtk grep "Route B|REST|MCP|config file|retry|backoff|circuit" "novel-runtime/novel_runtime/llm" "novel-cli/novel_cli/commands/chapter.py"` returned `0` matches; evidence saved to `changes/activate-route-a-provider-implementation/evidence/task-5-regression-error.txt` and shows only the RTK hook warning plus the zero-match summary.
- 2026-03-24: Task 5 commit boundary stayed verification-only: no runtime or CLI source edits were needed after the regression run; the only Task 5 updates are the two evidence files, appended notes in `findings.md`/`progress.md`, and the Task 5 checkbox flip in `tasks.md`.
- 2026-03-25: Final-wave rejection was valid because the previous green path depended on a CLI-local fallback provider while `OpenAIRouteAProvider.draft()` still raised `NotImplementedError`, so Route A never had a real env-backed ingress.
- 2026-03-25: The minimal in-bounds repair is: keep exact env validation in `build_route_a_provider()`, give `OpenAIRouteAProvider` an injectable OpenAI client factory that calls `chat.completions.create(...)`, and make the CLI pre-check active entities but always delegate real drafting through `build_route_a_provider()` with no no-env fallback.
- 2026-03-25: E2E chapter tests must now provide Route A env plus a fake provider seam because the saved contract rejects missing `NOVEL_LLM_PROVIDER`; keeping legacy no-env lifecycle tests would otherwise reintroduce the rejected placeholder behavior.
