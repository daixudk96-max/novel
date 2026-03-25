# Activate Route A provider-by-env implementation

<!-- MERGED CONTEXT -->
<!-- MERGED CONTEXT|Problem Statement|Goal|Key Decisions -->
## MERGED CONTEXT

### Problem Statement
Route A is selected as the next active slice, but `novel chapter draft` still stops at placeholder scaffolding instead of reaching a real Novel-owned provider/API-by-env runtime path.

### Goal
Activate only the minimal Route A provider-by-env path inside Novel so `/start-work` can execute against a concrete runtime plan without widening CLI or external surfaces.

### Key Decisions
- Scope is Route A only: provider/API-by-env inside Novel.
- Env-only config for this slice: `NOVEL_LLM_PROVIDER`, `NOVEL_LLM_MODEL`, `NOVEL_LLM_API_KEY`.
- One concrete provider behind a narrow fakeable abstraction.
- Fail fast on missing/invalid env; no placeholder fallback.
- Fake-provider tests only; no live network.
- Resilience is seam-only here; Route B, REST, network service, MCP, and broader resilience stay out of scope.

### Source Alignment
- `changes/activate-route-a-provider-implementation/proposal.md`
- `architecture-novel-runtime-v1.md` Phase 3 Route A wording and readiness terminology

## TL;DR
> **Summary**: Turn Route A from placeholder drafting into the first real Novel-owned provider ingress by adding env-based provider resolution, draft temperature policy, runtime wiring, and exact fail-fast CLI behavior.
> **Deliverables**:
> - Runtime provider/config seam for Route A
> - Draft temperature policy
> - `ChapterDrafter` provider integration
> - `chapter draft` CLI wiring + exact error UX
> - Targeted TDD and regression verification
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: 1 → 2 → 3 → 4 → 5

## Context
### Original Request
Plan the next roadmap slice using the CLI/creating-changes planning workflow after the dual-route roadmap rewrite.

### Interview Summary
- User selected **Route A** as the next active slice.
- Route A remains Novel-owned provider/API-by-env execution.
- Route B, REST/network-service/MCP, and broad resilience stay out of scope.

### Metis Review (gaps addressed)
- Locked env-only config source for this slice.
- Locked fail-fast behavior instead of placeholder fallback.
- Locked one concrete provider behind a narrow abstraction.
- Locked fake-provider tests only; no live network.
- Locked resilience to seam-only unless absolutely required.

## Work Objectives
### Core Objective
Make `novel chapter draft` use a real Route A runtime provider path while keeping the rest of the shared lifecycle unchanged.

### Deliverables
- `novel_runtime/llm/provider.py` + package init
- `novel_runtime/llm/temperature.py`
- Updated `novel_runtime/pipeline/drafter.py`
- Updated `novel_cli/novel_cli/commands/chapter.py`
- New/updated tests in `tests/test_drafter.py` and `tests/test_cli_chapter.py`

### Definition of Done
- `rtk python -m pytest tests/test_drafter.py`
- `rtk python -m pytest tests/test_cli_chapter.py -k draft`
- `rtk python -m pytest tests/test_cli_e2e.py -k chapter`
- `chapter draft` no longer relies on placeholder-only behavior when valid Route A env is present.
- Invalid/missing Route A env fails with exact plain/json CLI errors.

### Must Have
- Env vars: `NOVEL_LLM_PROVIDER`, `NOVEL_LLM_MODEL`, `NOVEL_LLM_API_KEY`
- Exact precedence rule: env-only; no new flags/config files
- Fakeable provider abstraction
- Draft temperature policy separate from drafter logic
- No live network tests

### Must NOT Have
- No Route B work
- No REST / network service / MCP work
- No plugin/provider platform
- No broad resilience/retry/backoff implementation
- No hidden skill logic

## Verification Strategy
> ZERO HUMAN INTERVENTION — all verification is agent-executed.
- Test decision: TDD + pytest
- QA policy: Every task includes exact agent-run verification
- Evidence: `changes/activate-route-a-provider-implementation/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
Wave 1: config contract + drafter contract + temperature policy plan
Wave 2: CLI wiring + regression verification + scope guardrails

### Dependency Matrix
- 1 blocks 2, 3, 4, 5
- 2 blocks 3, 4
- 3 blocks 4, 5
- 4 blocks 5
- 5 blocks final verification

### Agent Dispatch Summary
- Wave 1 → 3 tasks → `deep`, `writing`
- Wave 2 → 2 tasks → `general`, `deep`

## TODOs

- [x] 1. Freeze the Route A env/config contract and failing-first tests

  **What to do**: Add failing tests that define the Route A config contract before any implementation. Lock env-only resolution, one-provider scope, and exact failure behavior for unsupported provider, missing key, invalid model presence, and invalid temperature input.
  **Must NOT do**: Do not implement live provider calls. Do not add CLI flags or config-file fallbacks.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: test contract defines the whole slice.
  - Skills: `[]` — contract is repo-local.
  - Omitted: `['artistry']` — not creative work.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2, 3, 4, 5 | Blocked By: none

  **References**:
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:25-53` — current draft CLI ingress that must preserve surface shape.
  - Pattern: `tests/test_drafter.py:10-66` — existing drafter contract pattern.
  - Pattern: `tests/test_cli_chapter.py:1097-1282` — existing draft CLI test style and exact JSON/plain assertions.
  - Pattern: `architecture-novel-runtime-v1.md:735-741` — Route A official scope.

  **Acceptance Criteria**:
  - [ ] `tests/test_drafter.py` includes failing cases for env/provider resolution and invalid temperature handling.
  - [ ] `tests/test_cli_chapter.py` includes failing cases for plain/json CLI error UX when Route A env is invalid.
  - [ ] Tests document env-only precedence and fail-fast behavior.

  **QA Scenarios**:
  ```
  Scenario: Route A config contract is frozen in tests
    Tool: Bash
    Steps: Run `rtk python -m pytest tests/test_drafter.py -k "provider or temperature or draft"`
    Expected: Failing-first or passing contract tests explicitly cover provider env, missing key, and invalid temperature cases.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-1-config-contract.txt

  Scenario: CLI error UX contract exists
    Tool: Bash
    Steps: Run `rtk python -m pytest tests/test_cli_chapter.py -k "draft and (json or entity or provider)"`
    Expected: Draft CLI tests assert exact plain/json failure outputs for Route A env errors.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-1-config-contract-error.txt
  ```

  **Commit**: YES | Message: `test(route-a): freeze env config and draft error contract` | Files: `tests/test_drafter.py`, `tests/test_cli_chapter.py`

- [x] 2. Implement the minimal Route A provider resolver in `novel_runtime/llm`

  **What to do**: Create `novel_runtime/llm/__init__.py` and `novel_runtime/llm/provider.py` with a narrow provider interface plus env-only resolver. Support exactly one concrete provider path behind the abstraction, and surface deterministic exceptions/messages for unsupported or incomplete configuration.
  **Must NOT do**: Do not add provider registry/discovery, config files, or network-service seams.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: introduces the core runtime contract.
  - Skills: `[]`
  - Omitted: `['writing']` — implementation-focused.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 3, 4 | Blocked By: 1

  **References**:
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:270-315` — existing helper/validation style for CLI-visible failures.
  - Pattern: `architecture-novel-runtime-v1.md:737-740` — required Route A provider/temperature/resilience vocabulary.
  - Test: `tests/test_drafter.py` — target contract to satisfy.

  **Acceptance Criteria**:
  - [ ] `novel_runtime/llm/provider.py` exposes a fakeable provider seam and env resolver.
  - [ ] Resolver uses only `NOVEL_LLM_PROVIDER`, `NOVEL_LLM_MODEL`, `NOVEL_LLM_API_KEY` for this slice.
  - [ ] Unsupported/missing config paths are deterministic and test-covered.

  **QA Scenarios**:
  ```
  Scenario: Provider resolver satisfies unit contract
    Tool: Bash
    Steps: Run `rtk python -m pytest tests/test_drafter.py -k "provider or env"`
    Expected: Resolver-backed tests pass with no live network dependency.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-2-provider-resolver.txt

  Scenario: No Route B or config-file drift appears
    Tool: Bash
    Steps: Run `rtk grep "config file|MCP|REST|Route B" "novel-runtime/novel_runtime/llm/provider.py"`
    Expected: No matches indicating out-of-scope expansion.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-2-provider-resolver-error.txt
  ```

  **Commit**: YES | Message: `feat(route-a): add env-only provider resolver seam` | Files: `novel-runtime/novel_runtime/llm/__init__.py`, `novel-runtime/novel_runtime/llm/provider.py`

- [x] 3. Add draft temperature policy and refactor `ChapterDrafter`

  **What to do**: Create `novel_runtime/llm/temperature.py`, validate/normalize temperature input there, and refactor `novel_runtime/pipeline/drafter.py` to call the provider seam while preserving the `ChapterDraft` contract. Keep runtime output-only and preserve current chapter/entity validation.
  **Must NOT do**: Do not change canonical-state mutation semantics or add retries/backoff logic.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: core runtime behavior change.
  - Skills: `[]`
  - Omitted: `['artistry']`

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 4, 5 | Blocked By: 1, 2

  **References**:
  - Pattern: `tests/test_drafter.py:10-66` — required `ChapterDraft` shape and entity validation behavior.
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:275-297` — chapter metadata mutation expects stable draft fields.
  - Pattern: `architecture-novel-runtime-v1.md:736-739` — Route A drafter/provider/temperature expectations.

  **Acceptance Criteria**:
  - [ ] `ChapterDrafter` still returns `chapter`, `title`, `status`, `summary`, `content`.
  - [ ] Active-world-entity guard remains intact.
  - [ ] Empty provider output and provider exceptions fail deterministically.
  - [ ] Temperature policy is separate from drafter logic and test-covered.

  **QA Scenarios**:
  ```
  Scenario: Drafter contract remains stable after provider integration
    Tool: Bash
    Steps: Run `rtk python -m pytest tests/test_drafter.py`
    Expected: All drafter tests pass, including structured output and error cases.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-3-drafter.txt

  Scenario: Temperature policy is explicit and isolated
    Tool: Bash
    Steps: Run `rtk grep "temperature" "novel-runtime/novel_runtime/llm/temperature.py" && rtk grep "temperature" "novel-runtime/novel_runtime/pipeline/drafter.py"`
    Expected: Temperature logic exists in the policy module and is consumed by the drafter.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-3-drafter-error.txt
  ```

  **Commit**: YES | Message: `refactor(route-a): wire drafter through provider and temperature policy` | Files: `novel-runtime/novel_runtime/llm/temperature.py`, `novel-runtime/novel_runtime/pipeline/drafter.py`

- [x] 4. Wire `chapter draft` to the Route A runtime path without widening the CLI surface

  **What to do**: Update `novel_cli/novel_cli/commands/chapter.py` so `chapter draft` uses the new runtime/provider path, keeps the existing JSON/plain output contract, and emits exact failure messages for Route A config/provider errors. Preserve all non-draft chapter commands unchanged.
  **Must NOT do**: Do not add new commands, prompts, interactive flows, or direct SDK construction in the CLI layer.

  **Recommended Agent Profile**:
  - Category: `general` — Reason: CLI wiring against existing patterns.
  - Skills: `[]`
  - Omitted: `['writing']`

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 5 | Blocked By: 2, 3

  **References**:
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:25-53` — current draft command surface to preserve.
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:307-315` — exact JSON-object validation/failure style.
  - Test: `tests/test_cli_chapter.py:1097-1282` — current draft CLI expectations.

  **Acceptance Criteria**:
  - [ ] `chapter draft --chapter N` still writes chapter files and updates chapter metadata.
  - [ ] `chapter draft --json` preserves existing payload keys.
  - [ ] Invalid Route A env/provider produces exact plain/json errors.
  - [ ] No unrelated chapter command behavior changes.

  **QA Scenarios**:
  ```
  Scenario: Draft CLI remains stable in plain and JSON modes
    Tool: Bash
    Steps: Run `rtk python -m pytest tests/test_cli_chapter.py -k draft`
    Expected: Draft command tests pass for file output, JSON payload, redraft behavior, and exact failures.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-4-cli-draft.txt

  Scenario: CLI surface does not widen
    Tool: Bash
    Steps: Run `rtk python -m pytest tests/test_cli_chapter.py -k help`
    Expected: Chapter help still reflects the same public command surface.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-4-cli-draft-error.txt
  ```

  **Commit**: YES | Message: `feat(route-a): wire chapter draft through provider-backed runtime` | Files: `novel-cli/novel_cli/commands/chapter.py`, `tests/test_cli_chapter.py`

- [x] 5. Run Route A regression and record explicit scope guardrails

  **What to do**: Run the targeted Route A and shared-lifecycle regressions, confirm no Route B/network-service/resilience drift entered the slice, and record exact evidence paths and commit boundaries.
  **Must NOT do**: Do not introduce live provider smoke tests or broad full-suite expansion unless targeted regressions fail.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: final regression + scope audit.
  - Skills: `[]`
  - Omitted: `['artistry']`

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: Final verification | Blocked By: 3, 4

  **References**:
  - Pattern: `tests/test_cli_chapter.py:1285-1485` — downstream settle/postcheck contract must remain intact.
  - Pattern: `architecture-novel-runtime-v1.md:783-798` — Route A readiness and explicit exclusions.
  - Pattern: `changes/make-chapter-draft-llm-executable/tasks.md` — existing Route A branch scope guardrails.

  **Acceptance Criteria**:
  - [ ] `tests/test_drafter.py` passes.
  - [ ] `tests/test_cli_chapter.py -k draft` passes.
  - [ ] `tests/test_cli_e2e.py -k chapter` passes.
  - [ ] Grep-based scope checks show no Route B/REST/MCP/plugin drift in Route A slice files.

  **QA Scenarios**:
  ```
  Scenario: Route A targeted regression stays green
    Tool: Bash
    Steps: Run `export PYTHONPATH="E:/github/novel/novel-cli;E:/github/novel/novel-runtime" && rtk python -m pytest tests/test_drafter.py tests/test_cli_chapter.py -k draft && rtk python -m pytest tests/test_cli_e2e.py -k chapter`
    Expected: All targeted Route A and chapter continuation checks pass.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-5-regression.txt

  Scenario: Route A slice stayed in bounds
    Tool: Bash
    Steps: Run `rtk grep "Route B|REST|MCP|config file|retry|backoff|circuit" "novel-runtime/novel_runtime/llm" "novel-cli/novel_cli/commands/chapter.py"`
    Expected: No out-of-scope implementation drift appears beyond the explicitly allowed narrow seam.
    Evidence: changes/activate-route-a-provider-implementation/evidence/task-5-regression-error.txt
  ```

  **Commit**: YES | Message: `test(route-a): verify provider draft path and scope guardrails` | Files: `changes/activate-route-a-provider-implementation/evidence/*`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- Commit 1: `test(route-a): freeze env config and draft error contract`
- Commit 2: `feat(route-a): add env-only provider resolver seam`
- Commit 3: `refactor(route-a): wire drafter through provider and temperature policy`
- Commit 4: `feat(route-a): wire chapter draft through provider-backed runtime`
- Commit 5: `test(route-a): verify provider draft path and scope guardrails`

## Success Criteria
- Route A becomes the first real provider-backed ingress without changing the shared-core lifecycle.
- Draft command behavior is deterministic in both success and failure paths.
- The implementation remains inside Novel-owned env/provider boundaries and does not absorb Route B or external-surface scope.
