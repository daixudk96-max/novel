# Findings: route-a-real-trigger-verification

## Task 1: Packaged CLI preflight and explicit `novel.exe` proof
- **Result**: PASS
- **Observable**: `py -3.12 -m pip install -e novel-runtime` and `py -3.12 -m pip install -e novel-cli` both succeeded from `E:/github/novel`.
- **Observable**: Explicit Python 3.12 Scripts path resolved to `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe`.
- **Observable**: Running that exact `novel.exe --help` succeeded and listed `chapter` among commands.
- **Decision**: `changes/route-a-real-trigger-verification/evidence/` and `changes/route-a-real-trigger-verification/runtime/` are the canonical roots for this Route A real-trigger plan.
- **Guardrail**: `py -3.12 -m novel_cli.main --help` was recorded as supplementary only; packaged-console-script proof remains the explicit Scripts-path `novel.exe` run.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-1-packaged-preflight.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-1-packaged-preflight-error.txt`

## Task 2: Offline `sitecustomize.py` fake-provider harness
- **Result**: PASS
- **Implementation**: `changes/route-a-real-trigger-verification/support/sitecustomize.py` patches `novel_runtime.llm.provider.build_route_a_provider` during Python startup and only activates the fake path when `NOVEL_REAL_VERIFY_FAKE_PROVIDER=1`.
- **Guardrail**: When inactive, the patch delegates to the original builder, so packaged `novel.exe --help` still starts normally and no provider call log is created.
- **Observable**: The fake provider reads `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE` with UTF-8 and returned `Provider-backed draft body.` for the packaged `chapter draft --chapter 1` smoke.
- **Observable**: The fake provider wrote `changes/route-a-real-trigger-verification/runtime/provider-call.json` with the exact prompt `Draft Chapter 1 about Mira. Summary: Mira takes the next step.` and `temperature` `1.0`.
- **Decision**: The harness still resolves the standard Route A provider config, so offline verification can stay within the existing `NOVEL_LLM_PROVIDER` / `NOVEL_LLM_MODEL` / `NOVEL_LLM_API_KEY` contract while avoiding live OpenAI imports.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-2-fake-provider-harness.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-2-fake-provider-harness-error.txt`

## Task 3: Deterministic Route A verification workspace bootstrap
- **Result**: PASS
- **Observable**: `runtime/no-project/`, `runtime/no-entity/`, `runtime/env-contract/`, `runtime/happy/`, and `runtime/redraft/` were recreated as isolated lanes under `changes/route-a-real-trigger-verification/runtime/`.
- **Observable**: Packaged `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe` seeded `no-entity`, `env-contract`, `happy`, and `redraft` via `project init mybook --genre fantasy`; only `env-contract`, `happy`, and `redraft` also ran `world entity add --name Mira --type character --attributes '{"role": "lead"}'`.
- **Guardrail**: `runtime/no-entity/mybook/canonical_state.json` keeps `world.entities` empty, preserving the later active-entity failure lane without hand-editing.
- **Guardrail**: `runtime/no-project/` was created only as an empty directory and still lacks both `.novel_project_path` and any `canonical_state.json`.
- **Decision**: Task 3 evidence captures both the packaged command transcript and the post-seed filesystem/state assertions, so later failure and success tasks can consume fixed workspace lanes without cross-contamination.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-3-workspace-bootstrap.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-3-workspace-bootstrap-error.txt`

## Task 4: No-project and active-entity guard failures
- **Result**: PASS
- **Observable**: In `runtime/no-project/`, packaged `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe --json chapter draft --chapter 1` exited `1` and emitted `{"code": 1, "error": "no novel project selected"}` with no project files created.
- **Observable**: In `runtime/no-entity/`, packaged `novel.exe chapter draft --chapter 1` exited `1` and emitted `Error: chapter 1 draft requires at least one active world entity`; the matching JSON run emitted `{"code": 1, "error": "chapter 1 draft requires at least one active world entity"}`.
- **Guardrail**: After both `runtime/no-entity/` failures, `mybook/canonical_state.json` still contains `chapters: []`, proving `_raise_fail()` stopped before any chapter write.
- **Guardrail**: Neither failure lane produced `mybook/chapters/chapter_1.md`; `runtime/no-project/` remained empty and `runtime/no-entity/` preserved only the pre-seeded selection/state files.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-4-no-project-and-entity-guard.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-4-no-project-and-entity-guard-error.txt`

## Task 5: Missing-provider and unsupported-provider fail-fast contracts
- **Result**: PASS
- **Observable**: In `runtime/env-contract/`, packaged `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe chapter draft --chapter 1` with Route A env vars unset exited `1` and emitted `Error: NOVEL_LLM_PROVIDER is required for Route A provider resolution`; the matching JSON run emitted `{"code": 1, "error": "NOVEL_LLM_PROVIDER is required for Route A provider resolution"}`.
- **Observable**: With `NOVEL_LLM_PROVIDER=anthropic`, `NOVEL_LLM_MODEL=claude-3-7-sonnet`, and `NOVEL_LLM_API_KEY=test-key`, the packaged plain run emitted `Error: unsupported Route A provider 'anthropic'; expected NOVEL_LLM_PROVIDER='openai'`, and the matching JSON run emitted `{"code": 1, "error": "unsupported Route A provider 'anthropic'; expected NOVEL_LLM_PROVIDER='openai'"}`.
- **Guardrail**: `runtime/env-contract/mybook/chapters/chapter_1.md` remained absent after all four provider-selection failures, and the workspace still lacks any `chapters/` directory.
- **Guardrail**: `runtime/env-contract/mybook/canonical_state.json` still contains `chapters: []`, confirming provider resolution failed before any chapter mutation.
- **Decision**: Real packaged-CLI behavior matches the repo-frozen Route A provider-selection contracts in `resolve_route_a_provider_config()` for both plain and JSON output modes.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-5-provider-env-contract.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-5-provider-env-contract-error.txt`

## Task 6: Missing-model and missing-API-key fail-fast contracts
- **Result**: PASS
- **Observable**: In `runtime/env-contract`, packaged `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe chapter draft --chapter 1` with `NOVEL_LLM_PROVIDER=openai`, `NOVEL_LLM_MODEL=gpt-4o-mini`, and no API key exited `1` and emitted `Error: NOVEL_LLM_API_KEY is required when NOVEL_LLM_PROVIDER='openai'`; the matching JSON run emitted `{"code": 1, "error": "NOVEL_LLM_API_KEY is required when NOVEL_LLM_PROVIDER='openai'"}`.
- **Observable**: With `NOVEL_LLM_PROVIDER=openai`, `NOVEL_LLM_API_KEY=test-key`, and no model, the packaged plain run emitted `Error: NOVEL_LLM_MODEL is required when NOVEL_LLM_PROVIDER='openai'`, and the matching JSON run emitted `{"code": 1, "error": "NOVEL_LLM_MODEL is required when NOVEL_LLM_PROVIDER='openai'"}`.
- **Observable**: With `NOVEL_LLM_PROVIDER=openai`, `NOVEL_LLM_MODEL='   '`, and `NOVEL_LLM_API_KEY=test-key`, the packaged plain run emitted the same missing-model contract, matching `_normalize_value()` trim behavior.
- **Guardrail**: `runtime/env-contract/mybook/chapters/chapter_1.md` remained absent after all five missing-field commands, and `mybook/` still contains only `canonical_state.json` and `canonical_state.json.lock`.
- **Guardrail**: `runtime/env-contract/mybook/canonical_state.json` still contains `chapters: []`, confirming missing-field provider validation fails before any chapter mutation.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-6-provider-missing-fields.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-6-provider-missing-fields-error.txt`

## Task 7: Happy-path plain-mode drafting and real file/state side effects
- **Result**: PASS
- **Observable**: In `runtime/happy/`, packaged `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe chapter draft --chapter 1` exited `0` and emitted `Drafted chapter 1 at E:\github\novel\changes\route-a-real-trigger-verification\runtime\happy\mybook\chapters\chapter_1.md` in plain mode.
- **Observable**: With `PYTHONPATH=E:/github/novel/changes/route-a-real-trigger-verification/support`, `NOVEL_REAL_VERIFY_FAKE_PROVIDER=1`, and `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE` pointed at `runtime/happy/fake-draft.txt`, `runtime/happy/mybook/chapters/chapter_1.md` was written as the exact sentinel body `Provider-backed draft body.`.
- **Observable**: `runtime/happy/mybook/canonical_state.json` now contains one chapter record with `number=1`, `title="Chapter 1"`, `status="draft"`, `summary="Mira takes the next step."`, and `settled_at=""`.
- **Observable**: `changes/route-a-real-trigger-verification/runtime/provider-call.json` captured the exact Route A prompt `Draft Chapter 1 about Mira. Summary: Mira takes the next step.` and `temperature` `1.0`.
- **Guardrail**: The written chapter body is not equal to the placeholder scaffold `# Chapter 1\n\nMira takes the next step.\n`, proving the installed CLI reached the fake provider rather than placeholder-only drafting.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-7-happy-path-plain.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-7-happy-path-plain-error.txt`

## Task 8: Happy-path JSON parity and repeat-draft `settled_at` reset
- **Result**: PASS
- **Observable**: In `runtime/happy/`, packaged `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe --json chapter draft --chapter 2` exited `0` and emitted a JSON payload containing `chapter`, `title`, `status`, `summary`, and absolute `path` values for chapter 2.
- **Observable**: With `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE` pointed at `runtime/happy/fake-draft-json.txt`, `runtime/happy/mybook/chapters/chapter_2.md` was written as the exact second sentinel body `Provider-backed JSON draft body.`.
- **Observable**: `runtime/happy/mybook/canonical_state.json` now contains the chapter 2 draft record `{"number": 2, "title": "Chapter 2", "status": "draft", "summary": "Mira takes the next step.", "settled_at": ""}`, which matches the same semantic metadata contract proven by the plain-mode chapter 1 run.
- **Observable**: `changes/route-a-real-trigger-verification/runtime/provider-call.json` captured the exact chapter 2 Route A prompt `Draft Chapter 2 about Mira. Summary: Mira takes the next step.` and `temperature` `1.0` during the JSON-mode run.
- **Observable**: In `runtime/redraft/`, pre-seeding chapter 1 as `status="settled"` with `settled_at="2026-03-22T12:34:56Z"` and rerunning packaged `novel.exe chapter draft --chapter 1` replaced that record with `status="draft"`, `summary="Mira takes the next step."`, and `settled_at=""` while writing `Provider-backed draft body.` to `chapter_1.md`.
- **Decision**: Plain-mode and JSON-mode success parity is semantic, not byte-identical; both packaged runs exit `0`, persist the same draft chapter contract, write the configured fake-provider body, and log the expected prompt plus `temperature=1.0`.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-8-happy-path-json-and-redraft.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-8-happy-path-json-and-redraft-error.txt`

## Task 9: Cleanup, repeatability, and verifier gate
- **Result**: PASS
- **Observable**: Cleanup removed ephemeral chapter outputs and the temporary harness-smoke files, while retaining workspace manifests, fake draft fixtures, and `runtime/provider-call.json`.
- **Observable**: The representative failure rerun in `runtime/no-entity` still exited `1` with `{"code": 1, "error": "chapter 1 draft requires at least one active world entity"}` and wrote nothing.
- **Observable**: The representative success rerun in `runtime/happy` still exited `0` with `Drafted chapter 1 at E:\github\novel\changes\route-a-real-trigger-verification\runtime\happy\mybook\chapters\chapter_1.md` after restoring the offline harness.
- **Observable**: `tools/verify-structure.sh` passed with zero failures.
- **Decision**: The verifier is repeatable after cleanup, and the evidence chain is complete through Task 9.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-9-verification-ledger.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-9-verification-ledger-error.txt`

## Task 4 extension: Packaged Route A resilience recovery and exhaustion
- **Result**: PASS
- **Implementation**: `changes/route-a-real-trigger-verification/support/sitecustomize.py` now accepts `NOVEL_REAL_VERIFY_RETRY_SEQUENCE` so the existing offline harness can deterministically raise retryable `APIConnectionError`, `APITimeoutError`, `InternalServerError`, or `RateLimitError` outcomes before eventual success.
- **Implementation**: `changes/route-a-real-trigger-verification/support/task_4_packaged_resilience.py` seeds fresh `runtime/retry-recovery/` and `runtime/retry-exhaustion/` lanes through the packaged Python 3.12 Scripts `novel.exe` path, injects the worktree `novel-cli` / `novel-runtime` code through `PYTHONPATH`, and writes task-specific evidence under the existing evidence tree.
- **Observable**: Recovery proof used packaged `C:\Users\daixu\AppData\Local\Programs\Python\Python312\Scripts\novel.exe chapter draft --chapter 1` with `NOVEL_REAL_VERIFY_RETRY_SEQUENCE=APIConnectionError,success`; the call log recorded exactly two attempts, then `runtime/retry-recovery/mybook/chapters/chapter_1.md` and `canonical_state.json` showed exactly one coherent chapter artifact/state write.
- **Observable**: Exhaustion proof used packaged plain and JSON `chapter draft --chapter 1` runs with `NOVEL_REAL_VERIFY_RETRY_SEQUENCE=APIConnectionError,RateLimitError,InternalServerError`; both runs exhausted the frozen 3-attempt budget and emitted the stable `chapter draft failed after 3 attempts:` contract.
- **Guardrail**: `runtime/retry-exhaustion/mybook/canonical_state.json` kept `chapters: []`, `runtime/retry-exhaustion/mybook/chapters/chapter_1.md` never appeared, and both exhaustion call logs recorded the same three retryable attempts, proving zero partial writes.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-4-packaged-resilience-recovery.txt`
  - `changes/route-a-real-trigger-verification/evidence/task-4-packaged-resilience-exhaustion.txt`

## Final-wave repair: worktree-only packaged proof and clutter cleanup
- **Result**: PASS
- **Implementation**: Added `changes/route-a-real-trigger-verification/support/task_4_worktree_packaged_preflight.py` to prove the explicit Python 3.12 Scripts `novel.exe` entrypoint runs against the active worktree code path via `PYTHONPATH=<worktree support>;<worktree novel-cli>;<worktree novel-runtime>`.
- **Observable**: `changes/route-a-real-trigger-verification/evidence/task-4-packaged-worktree-preflight.txt` captures packaged `novel.exe --help`, then packaged plain/JSON `chapter draft --chapter 1` fail-fast provider-env errors from a seeded worktree-only workspace with `NOVEL_LLM_PROVIDER`, `NOVEL_LLM_MODEL`, and `NOVEL_LLM_API_KEY` unset.
- **Guardrail**: The worktree preflight lane kept `mybook/canonical_state.json` with `chapters: []` and never created `mybook/chapters/chapter_1.md`, proving the fail-fast env path stayed offline and side-effect free beyond seeded project/entity setup.
- **Cleanup**: Removed out-of-scope worktree clutter at the repo root (`.novel_project_path`, `assistant-result.json`, `canonical_state.json`, `canonical_state.json.lock`, `artifacts/`), deleted `.claude/tdd-guard/data/test.json`, and removed `__pycache__/` directories under `tests/`, `novel-cli/`, `novel-runtime/`, and `changes/route-a-real-trigger-verification/support/`.
- **Evidence**:
  - `changes/route-a-real-trigger-verification/evidence/task-4-packaged-worktree-preflight.txt`
