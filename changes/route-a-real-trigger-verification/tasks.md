# Route A real trigger verification

## TL;DR
> **Summary**: Prove the finished Route A `chapter draft` slice through the packaged `novel.exe` entrypoint, using real CLI invocations, real filesystem side effects, and an offline fake-provider harness instead of live OpenAI traffic.
> **Deliverables**:
> - Packaged-CLI preflight and explicit `novel.exe` path evidence
> - Offline `sitecustomize.py` fake-provider harness for installed-CLI runs
> - Isolated Route A verification workspaces and evidence transcripts
> - Fail-fast error matrix for project/entity/env/provider contracts
> - Happy-path plain/JSON success proof plus repeat-draft state-reset proof
> - Final verification ledger, cleanup proof, and structure-gate result
> **Effort**: Medium
> **Parallel**: YES - 3 waves
> **Critical Path**: 1 → 2 → 3 → 4/5/6 → 7/8 → 9

## Context
### Original Request
指定一个真实验证计划吧

### Interview Summary
- Verification target is the completed Route A `novel chapter draft` slice.
- Verification must stay inside the existing Route A boundary: real CLI-triggered behavior, no live network, no live OpenAI.
- The user selected the recommended boundary: packaged CLI + offline fake-provider seam.

### Metis Review (gaps addressed)
- Explicitly lock packaged-console-script proof instead of `CliRunner` or in-process imports.
- Make the fake-provider seam a visible prerequisite, not a hidden assumption.
- Separate workspaces for no-project, no-entity, env-failure, happy-path, and repeat-draft runs to prevent cross-contamination.
- Require no-partial-write assertions for every failure scenario.
- Add verification-of-verification at the end so setup, evidence, and cleanup cannot silently drift.

## Work Objectives
### Core Objective
Produce and execute a decision-complete Route A real-trigger verification layer that proves the installed `novel.exe` entrypoint honors the approved draft success/failure contracts without using a live provider.

### Deliverables
- `changes/route-a-real-trigger-verification/support/sitecustomize.py`
- `changes/route-a-real-trigger-verification/findings.md`
- `changes/route-a-real-trigger-verification/progress.md`
- `changes/route-a-real-trigger-verification/evidence/*.txt`
- `changes/route-a-real-trigger-verification/runtime/*` working directories and harness logs

### Definition of Done
- `py -3.12 -m pip install -e novel-runtime && py -3.12 -m pip install -e novel-cli`
- Explicit Python 3.12 Scripts `novel.exe` path is resolved via `py -3.12 -c "import pathlib, sysconfig; print(pathlib.Path(sysconfig.get_path('scripts')) / 'novel.exe')"`
- Every planned failure scenario is proven through packaged `novel.exe` output plus no-partial-write assertions.
- Every planned success scenario is proven through packaged `novel.exe` output plus real file/state side effects.
- Evidence exists for plain mode, JSON mode, repeat-draft state reset, cleanup, and final ledger summary.

### Must Have
- Real packaged-console-script proof through `novel.exe`, not `CliRunner`
- Offline fake-provider injection through `sitecustomize.py`
- Real workspaces and file side effects under `changes/route-a-real-trigger-verification/runtime/`
- Exact approved Route A env vars: `NOVEL_LLM_PROVIDER`, `NOVEL_LLM_MODEL`, `NOVEL_LLM_API_KEY`
- Exact approved error strings and JSON error payloads where the repo already freezes them
- Evidence capture for exit code, stdout, stderr or combined visible output, and filesystem outcome

### Must NOT Have
- No live OpenAI call
- No live network smoke
- No Route B / MCP / REST scope
- No `CliRunner`-only proof
- No hidden helper assumptions that are not written into the verification harness
- No acceptance criteria that require a human to visually inspect and guess pass/fail

## Verification Strategy
> ZERO HUMAN INTERVENTION — all verification is agent-executed.
- Test decision: real packaged CLI verification with offline harness + filesystem assertions
- QA policy: every task includes exact command-trigger steps and explicit evidence files
- Evidence root: `changes/route-a-real-trigger-verification/evidence/`
- Runtime workspaces: `changes/route-a-real-trigger-verification/runtime/`

## Execution Strategy
### Parallel Execution Waves
Wave 1: packaged CLI preflight + fake-provider harness + isolated workspaces
Wave 2: packaged failure-matrix verification
Wave 3: packaged success-path verification + ledger + cleanup

### Dependency Matrix
- 1 blocks 2, 3, 4, 5, 6, 7, 8, 9
- 2 blocks 4, 5, 6, 7, 8, 9
- 3 blocks 4, 5, 6, 7, 8, 9
- 4 blocks 9
- 5 blocks 9
- 6 blocks 9
- 7 blocks 8, 9
- 8 blocks 9

### Agent Dispatch Summary
- Wave 1 → 3 tasks → `general`, `deep`
- Wave 2 → 3 tasks → `deep`, `general`
- Wave 3 → 3 tasks → `general`, `deep`, `writing`

## TODOs
> Verification work only. Do not change runtime or CLI behavior. Add only verification harness/support files and evidence under `changes/route-a-real-trigger-verification/`.

- [x] 1. Lock packaged CLI preflight and explicit `novel.exe` path proof

  **What to do**: Install `novel-runtime` and `novel-cli` into Python 3.12, resolve the exact `novel.exe` path from `sysconfig.get_path("scripts")`, prove `--help` runs from that explicit path, and record the canonical verification environment and evidence directories.
  **Must NOT do**: Do not accept bare `novel --help`, `py -3.12 -m novel_cli.main`, or `CliRunner` output as packaged-CLI proof.

  **Recommended Agent Profile**:
  - Category: `general` — Reason: shell/install/setup heavy, low ambiguity.
  - Skills: `['novel-dev-sop']` — packaged-console-script proof already has repo-local precedent.
  - Omitted: `['artistry']` — not visual work.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2-9 | Blocked By: none

  **References**:
  - Pattern: `changes/agent-callable-novel-cli/verification.md:15-25` — packaged-console-script-first proof model.
  - Pattern: `changes/agent-callable-novel-cli/verification.md:76-97` — exact explicit `novel.exe` discovery rule.
  - Pattern: `novel-cli/pyproject.toml:16-17` — console script is published as `novel = "novel_cli.main:cli"`.
  - Pattern: `skills/novel-dev-sop/references/sop-publish.md:19-20` — Python 3.12 Scripts path is the canonical smoke target.

  **Acceptance Criteria** (agent-executable only):
  - [ ] `py -3.12 -m pip install -e novel-runtime && py -3.12 -m pip install -e novel-cli` succeeds and transcript is saved to `changes/route-a-real-trigger-verification/evidence/task-1-packaged-preflight.txt`.
  - [ ] `py -3.12 -c "import pathlib, sysconfig; print(pathlib.Path(sysconfig.get_path('scripts')) / 'novel.exe')"` output is recorded as the only accepted packaged entrypoint.
  - [ ] Running that exact `novel.exe --help` succeeds and shows `chapter` in help output.
  - [ ] `changes/route-a-real-trigger-verification/evidence/` and `changes/route-a-real-trigger-verification/runtime/` exist as the canonical evidence and workspace roots.

  **QA Scenarios**:
  ```
  Scenario: Packaged console-script preflight passes
    Tool: Bash
    Steps:
      1. Run `py -3.12 -m pip install -e novel-runtime`.
      2. Run `py -3.12 -m pip install -e novel-cli`.
      3. Run `py -3.12 -c "import pathlib, sysconfig; print(pathlib.Path(sysconfig.get_path('scripts')) / 'novel.exe')"`.
      4. Run the resolved `novel.exe --help` and save the combined transcript to `changes/route-a-real-trigger-verification/evidence/task-1-packaged-preflight.txt`.
    Expected: The transcript shows successful installs, an explicit Python 3.12 Scripts `novel.exe` path, and help output containing `chapter`.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-1-packaged-preflight.txt

  Scenario: Non-canonical entrypoints are rejected as insufficient proof
    Tool: Bash
    Steps:
      1. Run `py -3.12 -m novel_cli.main --help`.
      2. Record that command and its output in `changes/route-a-real-trigger-verification/evidence/task-1-packaged-preflight-error.txt`.
      3. Mark the scenario as FAIL unless the explicit Scripts-path `novel.exe` proof from the first scenario also exists.
    Expected: The evidence file explicitly records that module invocation is supplementary only and cannot satisfy packaged-CLI proof by itself.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-1-packaged-preflight-error.txt
  ```

  **Commit**: YES | Message: `docs(route-a): add packaged real-trigger verification prerequisites` | Files: `changes/route-a-real-trigger-verification/findings.md`, `changes/route-a-real-trigger-verification/progress.md`

- [x] 2. Add the offline `sitecustomize.py` fake-provider harness for installed-CLI runs

  **What to do**: Create `changes/route-a-real-trigger-verification/support/sitecustomize.py` so packaged `novel.exe` runs can stay offline. The harness must patch `novel_runtime.llm.provider.build_route_a_provider` before CLI import, return a deterministic fake provider when `NOVEL_REAL_VERIFY_FAKE_PROVIDER=1`, and write a JSON call log containing `prompt` and `temperature` to the path in `NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG`.
  **Must NOT do**: Do not print from `sitecustomize.py`. Do not patch unrelated commands. Do not modify runtime or CLI source under `novel-runtime/` or `novel-cli/`.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: the harness must be precise and non-invasive.
  - Skills: `[]`
  - Omitted: `['writing']` — support code/harness precision matters more than prose.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 4-9 | Blocked By: 1

  **References**:
  - Pattern: `tests/test_drafter.py:119-168` — fake-provider and fake OpenAI client shape to preserve offline drafting semantics.
  - Pattern: `novel-runtime/novel_runtime/llm/provider.py:41-78` — current `build_route_a_provider()` contract to intercept.
  - External: `https://docs.python.org/3/library/site.html` — `site` is imported automatically during initialization and attempts to import `sitecustomize` unless Python starts with `-S`.

  **Acceptance Criteria** (agent-executable only):
  - [ ] `changes/route-a-real-trigger-verification/support/sitecustomize.py` exists and activates only when `NOVEL_REAL_VERIFY_FAKE_PROVIDER=1`.
  - [ ] The fake provider returns the exact text stored in `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE`.
  - [ ] The fake provider writes a JSON call log to `NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG` containing the exact `prompt` and `temperature` received.
  - [ ] With `PYTHONPATH="E:/github/novel/changes/route-a-real-trigger-verification/support"`, the packaged `novel.exe` path still reaches CLI startup without importing live OpenAI.

  **QA Scenarios**:
  ```
  Scenario: Installed CLI uses the offline fake-provider harness
    Tool: Bash
    Steps:
      1. Set `PYTHONPATH="E:/github/novel/changes/route-a-real-trigger-verification/support"`.
      2. Set `NOVEL_REAL_VERIFY_FAKE_PROVIDER=1`.
      3. Set `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE` to a UTF-8 text file containing `Provider-backed draft body.`.
      4. Set `NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG=E:/github/novel/changes/route-a-real-trigger-verification/runtime/provider-call.json`.
      5. In `changes/route-a-real-trigger-verification/runtime/harness-smoke`, run packaged `novel.exe project init mybook --genre fantasy`.
      6. In that same workspace, run packaged `novel.exe world entity add --name Mira --type character --attributes '{"role": "lead"}'`.
      7. Run packaged `novel.exe chapter draft --chapter 1`.
    Expected: The help command still works, the draft command stays offline, and `provider-call.json` is created with exact prompt/temperature fields.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-2-fake-provider-harness.txt

  Scenario: Harness remains inactive without the opt-in env switch
    Tool: Bash
    Steps:
      1. Unset `NOVEL_REAL_VERIFY_FAKE_PROVIDER`.
      2. Keep `PYTHONPATH` pointing at the support directory.
      3. Run packaged `novel.exe --help` and confirm no provider-call log file is created.
    Expected: CLI startup still works, but no fake-provider call log is produced because the harness did not activate.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-2-fake-provider-harness-error.txt
  ```

  **Commit**: YES | Message: `test(route-a): add packaged fake-provider harness` | Files: `changes/route-a-real-trigger-verification/support/sitecustomize.py`

- [x] 3. Bootstrap deterministic Route A verification workspaces

  **What to do**: Create isolated workspaces under `changes/route-a-real-trigger-verification/runtime/` and seed them through packaged `novel.exe` commands. `env-contract`, `happy`, and `redraft` must each contain a selected project plus one active entity named `Mira`; `no-entity` must contain a selected project with no active entity; `no-project` must remain empty on purpose.
  **Must NOT do**: Do not reuse one workspace across unrelated scenarios. Do not seed state with `CliRunner`. Do not hand-edit failure workspaces except where Task 8 explicitly requires a settled chapter fixture.

  **Recommended Agent Profile**:
  - Category: `general` — Reason: deterministic filesystem setup with packaged CLI commands.
  - Skills: `[]`
  - Omitted: `['artistry']`

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 4-9 | Blocked By: 1, 2

  **References**:
  - Pattern: `tests/test_cli_e2e.py:24-69` — packaged lifecycle setup uses `project init` followed by `world entity add` before `chapter draft`.
  - Pattern: `tests/test_cli_chapter.py:1111-1128` — active-entity seed required to reach env/provider validation.
  - Pattern: `changes/activate-route-a-provider-implementation/findings.md:35` — Windows `PYTHONPATH` must use `;` when multiple entries are required.

  **Acceptance Criteria** (agent-executable only):
  - [ ] `runtime/no-project/` stays empty except evidence files created by failing commands.
  - [ ] `runtime/no-entity/` contains `.novel_project_path` plus `mybook/canonical_state.json`, but no active entity.
  - [ ] `runtime/env-contract/`, `runtime/happy/`, and `runtime/redraft/` each contain a selected project plus active entity `Mira` created through packaged CLI commands.
  - [ ] Workspace bootstrap transcript is saved to `changes/route-a-real-trigger-verification/evidence/task-3-workspace-bootstrap.txt`.

  **QA Scenarios**:
  ```
  Scenario: Workspace bootstrap succeeds through packaged CLI commands
    Tool: Bash
    Steps:
      1. In each non-empty workspace, run packaged `novel.exe project init mybook --genre fantasy`.
      2. In `env-contract`, `happy`, and `redraft`, run packaged `novel.exe world entity add --name Mira --type character --attributes '{"role": "lead"}'`.
      3. Save the combined command transcript and resulting directory listing assertions to `changes/route-a-real-trigger-verification/evidence/task-3-workspace-bootstrap.txt`.
    Expected: All seeded workspaces contain the intended project marker/state files, and only the three success-path workspaces contain the active `Mira` entity.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-3-workspace-bootstrap.txt

  Scenario: Empty `no-project` workspace remains intentionally unseeded
    Tool: Bash
    Steps:
      1. Create `runtime/no-project/`.
      2. Do not run `project init` inside it.
      3. Record its initial directory listing before Task 4 runs.
    Expected: The workspace contains no project marker and no `canonical_state.json`, preserving an exact no-project failure lane.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-3-workspace-bootstrap-error.txt
  ```

  **Commit**: YES | Message: `docs(route-a): add real-trigger workspace bootstrap contract` | Files: `changes/route-a-real-trigger-verification/findings.md`, `changes/route-a-real-trigger-verification/progress.md`

- [x] 4. Verify no-project and active-entity guard failures through packaged CLI entrypoints

  **What to do**: Use `runtime/no-project/` and `runtime/no-entity/` to prove packaged `novel.exe` fails before any draft file write when project selection or active-entity prerequisites are missing. Cover both plain and JSON where the repo already freezes exact behavior.
  **Must NOT do**: Do not seed env-provider errors in these lanes. Task 4 is only for project-selection and entity-guard contracts.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: failure-path correctness plus no-partial-write assertions.
  - Skills: `[]`
  - Omitted: `['writing']`

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 9 | Blocked By: 1, 2, 3

  **References**:
  - Pattern: `tests/test_cli_chapter.py:1362-1395` — active-world-entity failure in plain and JSON modes.
  - Pattern: `tests/test_cli_chapter.py:1398-1412` — no-project failure is explicitly frozen in JSON mode.
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:29-35` — failure path routes through `_raise_fail()` before any file write.
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:281-292` — exact entity-guard logic and error string.

  **Acceptance Criteria** (agent-executable only):
  - [ ] `runtime/no-project/` packaged `novel.exe --json chapter draft --chapter 1` exits non-zero and emits `{ "error": "no novel project selected", "code": 1 }`.
  - [ ] `runtime/no-entity/` packaged `novel.exe chapter draft --chapter 1` exits non-zero and emits `Error: chapter 1 draft requires at least one active world entity`.
  - [ ] `runtime/no-entity/` packaged `novel.exe --json chapter draft --chapter 1` exits non-zero and emits the matching JSON error payload.
  - [ ] Neither workspace gains `mybook/chapters/chapter_1.md` after the failing commands.

  **QA Scenarios**:
  ```
  Scenario: No-project and no-entity failures are exact and side-effect free
    Tool: Bash
    Steps:
      1. In `runtime/no-project`, run packaged `novel.exe --json chapter draft --chapter 1`.
      2. In `runtime/no-entity`, run packaged `novel.exe chapter draft --chapter 1`.
      3. In `runtime/no-entity`, run packaged `novel.exe --json chapter draft --chapter 1`.
      4. Record exit codes, visible output, and file listings in `changes/route-a-real-trigger-verification/evidence/task-4-no-project-and-entity-guard.txt`.
    Expected: All three commands fail with the approved contracts and create no chapter files.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-4-no-project-and-entity-guard.txt

  Scenario: Failure lanes leave chapter state untouched
    Tool: Bash
    Steps:
      1. Read `runtime/no-entity/mybook/canonical_state.json` after both failures.
      2. Assert `chapters` is still `[]`.
      3. Assert `runtime/no-project/` still lacks any project or chapter files.
    Expected: Both failure lanes prove no partial state mutation.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-4-no-project-and-entity-guard-error.txt
  ```

  **Commit**: NO | Message: `n/a` | Files: `changes/route-a-real-trigger-verification/evidence/task-4-no-project-and-entity-guard*.txt`

- [x] 5. Verify missing-provider and unsupported-provider fail-fast contracts

  **What to do**: In `runtime/env-contract/`, use the active-entity project to verify the two top-level Route A provider-selection errors: missing `NOVEL_LLM_PROVIDER` and unsupported `NOVEL_LLM_PROVIDER=anthropic`. Cover plain and JSON output and assert zero partial writes.
  **Must NOT do**: Do not mix missing model or missing API key into this task. Those belong to Task 6.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: exact error contract validation.
  - Skills: `[]`
  - Omitted: `['artistry']`

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 9 | Blocked By: 1, 2, 3

  **References**:
  - Pattern: `tests/test_cli_chapter.py:1283-1320` — missing-provider plain and JSON outputs plus no-write assertions.
  - Pattern: `tests/test_cli_chapter.py:1415-1506` — unsupported-provider plain and JSON outputs plus no-write assertions.
  - Pattern: `novel-runtime/novel_runtime/llm/provider.py:45-55` — exact missing-provider and unsupported-provider logic.

  **Acceptance Criteria** (agent-executable only):
  - [ ] With only the active-entity fixture present, packaged `novel.exe chapter draft --chapter 1` fails with `Error: NOVEL_LLM_PROVIDER is required for Route A provider resolution`.
  - [ ] Packaged `novel.exe --json chapter draft --chapter 1` fails with `{ "error": "NOVEL_LLM_PROVIDER is required for Route A provider resolution", "code": 1 }`.
  - [ ] With `NOVEL_LLM_PROVIDER=anthropic`, `NOVEL_LLM_MODEL=claude-3-7-sonnet`, and `NOVEL_LLM_API_KEY=test-key`, plain and JSON outputs fail with the approved unsupported-provider message.
  - [ ] `runtime/env-contract/mybook/chapters/chapter_1.md` does not exist after any command in this task.

  **QA Scenarios**:
  ```
  Scenario: Missing and unsupported provider failures are exact through packaged CLI
    Tool: Bash
    Steps:
      1. In `runtime/env-contract`, run packaged `novel.exe chapter draft --chapter 1` with all Route A env unset.
      2. Run packaged `novel.exe --json chapter draft --chapter 1` with all Route A env unset.
      3. Set `NOVEL_LLM_PROVIDER=anthropic`, `NOVEL_LLM_MODEL=claude-3-7-sonnet`, `NOVEL_LLM_API_KEY=test-key`.
      4. Run packaged plain and JSON draft commands again.
      5. Save outputs and exit codes to `changes/route-a-real-trigger-verification/evidence/task-5-provider-env-contract.txt`.
    Expected: All four failures match the approved plain/JSON contracts and create no chapter file.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-5-provider-env-contract.txt

  Scenario: Provider-selection failures leave chapter metadata empty
    Tool: Bash
    Steps:
      1. Read `runtime/env-contract/mybook/canonical_state.json` after the four commands.
      2. Assert `chapters` remains `[]`.
    Expected: Fail-fast provider-selection errors occur before any chapter mutation.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-5-provider-env-contract-error.txt
  ```

  **Commit**: NO | Message: `n/a` | Files: `changes/route-a-real-trigger-verification/evidence/task-5-provider-env-contract*.txt`

- [x] 6. Verify missing-model and missing-API-key fail-fast contracts

  **What to do**: In `runtime/env-contract/`, verify the missing-field provider errors after setting `NOVEL_LLM_PROVIDER=openai`. Cover plain and JSON output for both missing `NOVEL_LLM_MODEL` and missing `NOVEL_LLM_API_KEY`. Also include one whitespace-trim edge proving a whitespace-only model value collapses to the same missing-model error.
  **Must NOT do**: Do not reuse the unsupported-provider lane from Task 5. Do not permit chapter-file creation in this workspace.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: exact missing-field contract plus normalization edge.
  - Skills: `[]`
  - Omitted: `['writing']`

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 9 | Blocked By: 1, 2, 3

  **References**:
  - Pattern: `tests/test_cli_chapter.py:1439-1554` — missing API key/model plain and JSON outputs plus no-write assertions.
  - Pattern: `novel-runtime/novel_runtime/llm/provider.py:57-65` — missing model and missing API key messages.
  - Pattern: `novel-runtime/novel_runtime/llm/provider.py:81-90` — provider/model/api-key values are trimmed before validation.

  **Acceptance Criteria** (agent-executable only):
  - [ ] With `NOVEL_LLM_PROVIDER=openai` and `NOVEL_LLM_MODEL=gpt-4o-mini` but no API key, packaged plain and JSON draft commands fail with the approved missing-key contract.
  - [ ] With `NOVEL_LLM_PROVIDER=openai` and `NOVEL_LLM_API_KEY=test-key` but no model, packaged plain and JSON draft commands fail with the approved missing-model contract.
  - [ ] With `NOVEL_LLM_PROVIDER=openai`, `NOVEL_LLM_MODEL='   '`, and `NOVEL_LLM_API_KEY=test-key`, packaged plain draft fails with the same missing-model contract.
  - [ ] `runtime/env-contract/mybook/chapters/chapter_1.md` still does not exist after all commands in this task.

  **QA Scenarios**:
  ```
  Scenario: Missing model and API key fail fast in plain and JSON modes
    Tool: Bash
    Steps:
      1. In `runtime/env-contract`, set `NOVEL_LLM_PROVIDER=openai` and `NOVEL_LLM_MODEL=gpt-4o-mini`, unset `NOVEL_LLM_API_KEY`, then run packaged plain and JSON draft commands.
      2. Set `NOVEL_LLM_PROVIDER=openai` and `NOVEL_LLM_API_KEY=test-key`, unset `NOVEL_LLM_MODEL`, then run packaged plain and JSON draft commands.
      3. Save outputs and exit codes to `changes/route-a-real-trigger-verification/evidence/task-6-provider-missing-fields.txt`.
    Expected: All four failures match the approved contracts and create no chapter file.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-6-provider-missing-fields.txt

  Scenario: Whitespace-only model value trims to missing-model failure
    Tool: Bash
    Steps:
      1. In `runtime/env-contract`, set `NOVEL_LLM_PROVIDER=openai`, `NOVEL_LLM_MODEL='   '`, and `NOVEL_LLM_API_KEY=test-key`.
      2. Run packaged `novel.exe chapter draft --chapter 1`.
      3. Record the exact output and no-write assertion in `changes/route-a-real-trigger-verification/evidence/task-6-provider-missing-fields-error.txt`.
    Expected: The command fails with `Error: NOVEL_LLM_MODEL is required when NOVEL_LLM_PROVIDER='openai'` and creates no chapter file.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-6-provider-missing-fields-error.txt
  ```

  **Commit**: NO | Message: `n/a` | Files: `changes/route-a-real-trigger-verification/evidence/task-6-provider-missing-fields*.txt`

- [x] 7. Verify happy-path plain-mode drafting and real file/state side effects

  **What to do**: In `runtime/happy/`, activate the offline harness through `PYTHONPATH`, seed the fake draft body via `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE`, set the approved Route A env vars, run packaged `novel.exe chapter draft --chapter 1`, and prove the visible output, file write, chapter metadata, and provider-call log are all correct.
  **Must NOT do**: Do not use JSON mode in this task. Do not accept the default placeholder text as proof; the fake-provider sentinel text must appear in the written file.

  **Recommended Agent Profile**:
  - Category: `general` — Reason: packaged CLI happy-path run with deterministic assertions.
  - Skills: `[]`
  - Omitted: `['artistry']`

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 8, 9 | Blocked By: 1, 2, 3

  **References**:
  - Pattern: `tests/test_cli_chapter.py:1097-1152` — plain-mode success output, file path, and chapter metadata contract.
  - Pattern: `tests/test_cli_chapter.py:1323-1359` — provider call prompt/temperature capture expectations.
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:37-55` — chapter file write and success payload text.
  - Pattern: `tests/test_drafter.py:137-168` — provider call should receive `temperature=1.0` and the exact prompt string.

  **Acceptance Criteria** (agent-executable only):
  - [ ] Packaged plain-mode draft exits `0` and emits a line that starts with `Drafted chapter 1 at ` and ends with the resolved `mybook/chapters/chapter_1.md` path for `runtime/happy/`.
  - [ ] `runtime/happy/mybook/chapters/chapter_1.md` contains the exact fake-provider sentinel text from `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE`.
  - [ ] `runtime/happy/mybook/canonical_state.json` contains one chapter record with `number=1`, `title="Chapter 1"`, `status="draft"`, `summary="Mira takes the next step."`, `settled_at=""`.
  - [ ] `runtime/provider-call.json` contains `prompt="Draft Chapter 1 about Mira. Summary: Mira takes the next step."` and `temperature=1.0`.

  **QA Scenarios**:
  ```
  Scenario: Plain-mode happy path proves installed CLI, offline provider, and file side effects
    Tool: Bash
    Steps:
      1. In `runtime/happy`, set `PYTHONPATH="E:/github/novel/changes/route-a-real-trigger-verification/support"`.
      2. Set `NOVEL_REAL_VERIFY_FAKE_PROVIDER=1`.
      3. Write `Provider-backed draft body.` to `runtime/happy/fake-draft.txt` and set `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE` to that path.
      4. Set `NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG=E:/github/novel/changes/route-a-real-trigger-verification/runtime/provider-call.json`.
      5. Set `NOVEL_LLM_PROVIDER=openai`, `NOVEL_LLM_MODEL=gpt-4o-mini`, `NOVEL_LLM_API_KEY=test-key`.
      6. Run packaged `novel.exe chapter draft --chapter 1`.
      7. Read `mybook/chapters/chapter_1.md` and `mybook/canonical_state.json`.
    Expected: The command succeeds, the chapter file contains the sentinel text, chapter metadata is written correctly, and the provider-call log proves the exact prompt/temperature.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-7-happy-path-plain.txt

  Scenario: Happy-path proof rejects placeholder-only output
    Tool: Bash
    Steps:
      1. Compare `mybook/chapters/chapter_1.md` against the placeholder text `# Chapter 1\n\nMira takes the next step.\n`.
      2. Record the comparison and provider-call log contents.
    Expected: The file does not equal the placeholder scaffold and therefore proves the installed CLI reached the fake provider instead of placeholder-only drafting.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-7-happy-path-plain-error.txt
  ```

  **Commit**: NO | Message: `n/a` | Files: `changes/route-a-real-trigger-verification/evidence/task-7-happy-path-plain*.txt`

- [x] 8. Verify happy-path JSON parity and repeat-draft `settled_at` reset

  **What to do**: In `runtime/happy/`, prove JSON-mode success on `chapter 2` with the same offline harness and compare its semantic outcomes against the plain-mode run. In `runtime/redraft/`, seed a settled chapter record by editing `mybook/canonical_state.json`, then rerun packaged `novel.exe chapter draft --chapter 1` and verify `settled_at` resets to an empty string.
  **Must NOT do**: Do not settle a chapter through Route B or live services. Do not treat byte-identical plain/JSON output as the requirement; parity is semantic outcome equivalence.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: parity and repeat-draft state mutation must be checked together.
  - Skills: `[]`
  - Omitted: `['artistry']`

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 9 | Blocked By: 1, 2, 3, 7

  **References**:
  - Pattern: `tests/test_cli_chapter.py:1154-1218` — JSON-mode success payload contract.
  - Pattern: `tests/test_cli_chapter.py:1221-1280` — rerunning draft on a settled chapter resets `settled_at`.
  - Pattern: `novel-cli/novel_cli/commands/chapter.py:295-317` — `_upsert_chapter()` resets `settled_at` on redraft.

  **Acceptance Criteria** (agent-executable only):
  - [ ] Packaged JSON-mode draft on `chapter 2` exits `0` and emits a JSON payload with `chapter`, `title`, `status`, `summary`, and absolute `path` keys matching the approved contract.
  - [ ] `runtime/happy/mybook/chapters/chapter_2.md` contains the second sentinel draft body and `canonical_state.json` contains a `draft` chapter 2 record.
  - [ ] `runtime/redraft/mybook/canonical_state.json` can be preseeded with chapter 1 `status="settled"` and non-empty `settled_at`, then packaged redraft resets `settled_at` to `""`.
  - [ ] Provider-call logging still shows `temperature=1.0` and the correct prompt strings for chapters 1 and 2.

  **QA Scenarios**:
  ```
  Scenario: JSON-mode success matches plain-mode semantics
    Tool: Bash
    Steps:
      1. In `runtime/happy`, keep the offline harness active.
      2. Write `Provider-backed JSON draft body.` to a second sentinel file and point `NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE` at it.
      3. Run packaged `novel.exe --json chapter draft --chapter 2`.
      4. Parse the JSON payload, read `mybook/chapters/chapter_2.md`, and compare chapter 2 metadata in `canonical_state.json`.
    Expected: JSON mode succeeds with the approved payload keys, writes the sentinel text to the file, and produces the same semantic chapter metadata as plain mode.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-8-happy-path-json-and-redraft.txt

  Scenario: Redraft resets settled timestamp on an existing chapter record
    Tool: Bash
    Steps:
      1. Copy `runtime/happy/mybook` into `runtime/redraft/mybook`.
      2. Edit `runtime/redraft/mybook/canonical_state.json` so chapter 1 has `status="settled"` and `settled_at="2026-03-22T12:34:56Z"`.
      3. Run packaged `novel.exe chapter draft --chapter 1` with the offline harness still active.
      4. Read `runtime/redraft/mybook/canonical_state.json` after the command.
    Expected: Chapter 1 remains present, `status` becomes `draft`, `settled_at` becomes `""`, and the command still writes the fake-provider text to `chapter_1.md`.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-8-happy-path-json-and-redraft-error.txt
  ```

  **Commit**: NO | Message: `n/a` | Files: `changes/route-a-real-trigger-verification/evidence/task-8-happy-path-json-and-redraft*.txt`

- [x] 9. Consolidate evidence, prove cleanup/repeatability, and gate the verifier itself

  **What to do**: Build a final PASS/FAIL ledger from Tasks 1-8, verify that evidence files and call logs exist, clean ephemeral runtime files while retaining the evidence root, rerun one representative packaged failure and one representative packaged success after cleanup, and capture the final structure gate.
  **Must NOT do**: Do not delete the evidence directory. Do not mark verification complete without proving the verifier can be rerun after cleanup.

  **Recommended Agent Profile**:
  - Category: `writing` — Reason: final ledger and verification summary must be precise and audit-friendly.
  - Skills: `['novel-dev-sop']` — structure-gate and verification-log conventions already exist.
  - Omitted: `['artistry']`

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: Final verification | Blocked By: 1-8

  **References**:
  - Pattern: `changes/agent-callable-novel-cli/verification.md:170-182` — final stage/check/status/evidence report shape.
  - Pattern: `skills/novel-dev-sop/references/sop-test-doc.md` — append-only evidence logging discipline.
  - Pattern: `tools/verify-structure.sh` — final structure gate already used elsewhere in the repo.

  **Acceptance Criteria** (agent-executable only):
  - [ ] `changes/route-a-real-trigger-verification/evidence/` contains transcripts for Tasks 1-8 and a final ledger file `task-9-verification-ledger.txt`.
  - [ ] Cleanup removes ephemeral files under `runtime/` except the retained workspace manifests, fake draft text fixtures, and packaged evidence files that the ledger references.
  - [ ] One representative failure (`no-entity` or missing-provider) and one representative success (`chapter 1` or `chapter 2`) rerun successfully after cleanup preparation.
  - [ ] `tools/verify-structure.sh` passes and its output is captured.

  **QA Scenarios**:
  ```
  Scenario: Final ledger proves the verifier ran end-to-end
    Tool: Bash
    Steps:
      1. Build a table with Stage / Check / Status / Evidence / Notes in `changes/route-a-real-trigger-verification/evidence/task-9-verification-ledger.txt`.
      2. List Tasks 1-8, their PASS/FAIL results, and the exact evidence file paths.
      3. Record the retained `provider-call.json` and any cleanup transcript paths.
      4. Run `tools/verify-structure.sh` and append its output.
    Expected: The ledger proves setup, failure-path checks, success-path checks, cleanup, and structure gate all ran from one evidence chain.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-9-verification-ledger.txt

  Scenario: Representative success and failure still rerun after cleanup
    Tool: Bash
    Steps:
      1. After cleanup, rerun packaged `novel.exe --json chapter draft --chapter 1` in `runtime/no-entity`.
      2. After cleanup, rerun packaged `novel.exe chapter draft --chapter 1` in `runtime/happy` with the offline harness and sentinel draft text file restored.
      3. Save outputs, exit codes, and directory snapshots to `changes/route-a-real-trigger-verification/evidence/task-9-verification-ledger-error.txt`.
    Expected: The representative failure still fails exactly, the representative success still succeeds exactly, and cleanup did not break the verifier.
    Evidence: changes/route-a-real-trigger-verification/evidence/task-9-verification-ledger-error.txt
  ```

  **Commit**: YES | Message: `test(route-a): record packaged real-trigger verification results` | Files: `changes/route-a-real-trigger-verification/evidence/*`, `changes/route-a-real-trigger-verification/findings.md`, `changes/route-a-real-trigger-verification/progress.md`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit `okay` before completing.
> Do NOT auto-proceed after verification.
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- Commit 1: `docs(route-a): add packaged real-trigger verification prerequisites`
- Commit 2: `test(route-a): add packaged fake-provider harness`
- Commit 3: `docs(route-a): add real-trigger workspace bootstrap contract`
- Commit 4: `test(route-a): record fail-fast packaged verification evidence`
- Commit 5: `test(route-a): record packaged happy-path verification evidence`
- Commit 6: `test(route-a): record packaged real-trigger verification results`

## Success Criteria
- The packaged Python 3.12 `novel.exe` entrypoint is the verified proof target, not imports or `CliRunner`.
- Route A draft success is proven offline through a deterministic fake-provider harness with real file/state side effects.
- Route A draft failures are proven through exact approved plain/JSON contracts with zero partial writes.
- The verifier itself is repeatable after cleanup and leaves behind a complete evidence chain.
