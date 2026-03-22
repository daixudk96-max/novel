# Design: Make Chapter Continuation Executable

## Goal

Turn the roadmap’s chapter continuation flow from a partial, placeholder-backed contract into the first real business-executable continuation slice in the Python runtime/CLI stack.

## Roadmap Position

This change comes immediately after the completed foundation step in `changes/agent-callable-novel-cli`.

It is:

- the first business-capability execution slice after the agent-callable contract step,
- a P0 roadmap item (`章节续写流程`) rather than a new product direction,
- a continuation MVP, not the full continuation epic.

It is not:

- a restart of startup/new-book flow work,
- a host adaptation project,
- a REPL/UI/prompt-packaging effort,
- a full audit/revise/approve/export completion pass.

## Current State

### Existing continuation spine

The repo already contains the following Python implementation cluster:

- `novel-cli/novel_cli/commands/chapter.py`
  - `chapter draft`
  - `chapter settle`
  - `chapter postcheck`
- `novel-runtime/novel_runtime/pipeline/settler.py`
- `novel-runtime/novel_runtime/pipeline/postcheck.py`
- `novel-cli/novel_cli/commands/snapshot.py`

### Existing verification baseline

The following tests already give us a regression spine to build on:

- `tests/test_cli_chapter.py`
- `tests/test_settler.py`
- `tests/test_postcheck.py`
- `tests/test_cli_state_snapshot.py`
- `tests/test_cli_e2e.py`

### Current blocker

`chapter draft` in `novel-cli/novel_cli/commands/chapter.py` currently writes deterministic placeholder text and updates chapter state with a placeholder summary. That is enough for contract-shape proof, but not enough for real continuation readiness.

## Scope

### In scope

- Define the real chapter-draft MVP contract.
- Add runtime-backed draft behavior.
- Keep draft non-interactive and CLI-first.
- Preserve compatibility with settle/postcheck/snapshot.
- Extend tests to prove the continuation slice end-to-end.

### Out of scope

- startup/new-book outline flow,
- full audit/revise routing,
- approval/export,
- host-specific skill logic,
- REPL polish,
- new packaging/publish work unrelated to the draft MVP.

## Architecture

### Layer model

#### Runtime

Runtime must own the actual draft behavior. The draft implementation must not live only inside the CLI command body.

Expected runtime landing zone:

- `novel-runtime/novel_runtime/pipeline/drafter.py` (new or equivalent dedicated module)

The runtime draft layer should be responsible for:

- validating draft inputs,
- assembling the minimal required context,
- producing a chapter draft result object,
- returning structured data that the CLI can emit without prose parsing.

#### CLI

CLI remains the formal machine interface:

- `novel chapter draft --chapter ... [other required inputs] --json`

The CLI command should:

- resolve project state,
- call the runtime draft path,
- write the draft artifact(s),
- update canonical state as required,
- emit stable machine-readable output and stable failures.

#### Workflow

This change does not add new host logic. It only makes the existing roadmap continuation workflow less blocked by replacing the fake draft step with a real one.

## Draft MVP Contract

The MVP must answer one simple question honestly: what is the smallest real draft path that is meaningfully better than the placeholder but still feasible as the first execution slice?

The implementation plan should freeze:

- minimum required inputs,
- output file expectations,
- canonical state updates,
- expected JSON payload shape for draft success/failure,
- deterministic failure modes.

The draft contract must be strong enough that downstream steps can use it without relying on “placeholder-only” semantics.

## Proposed File Structure Changes

Expected touched files in execution (planned, not yet edited here):

- `novel-runtime/novel_runtime/pipeline/drafter.py` — new runtime draft MVP
- `novel-cli/novel_cli/commands/chapter.py` — switch CLI draft path to runtime-backed implementation
- `tests/test_cli_chapter.py` — draft contract and failure-path coverage
- `tests/test_cli_e2e.py` — real continuation path assertions
- possibly targeted runtime tests such as:
  - `tests/test_drafter.py`
  - or extension of existing chapter/runtime tests

Potentially relevant adjacent modules to mention in execution, but not necessarily modify immediately:

- `novel-runtime/novel_runtime/context/assembly.py`
- `novel-runtime/novel_runtime/context/visibility.py`
- `novel-runtime/novel_runtime/state/canonical.py`
- `novel-runtime/novel_runtime/state/snapshot.py`

## Key Decisions

1. **Continuation before startup**
   - justified by roadmap priority (P0 vs P1) and existing Python readiness.

2. **Draft MVP before full audit/revise**
   - the first execution slice should make the continuation loop real before broadening the loop.

3. **Runtime-owned draft logic**
   - no CLI-only fake behavior.

4. **Regression-first delivery**
   - baseline tests get locked before behavior changes.

5. **Thin vertical slice**
   - real draft + existing settle/postcheck/snapshot path, not the full epic.

## Edge Cases

- missing project context,
- missing required chapter prerequisites,
- invalid draft input payload,
- draft writes output but state update fails,
- draft succeeds but settle/postcheck expectations no longer match old placeholder assumptions.

Each of these needs explicit test coverage or explicit documented exclusion in the execution tasks.

## Risks

### Risk 1: Contract drift between draft and downstream steps

If draft output changes silently, settle/postcheck tests may keep passing only because they overwrite the draft file manually.

**Mitigation:** add e2e coverage that consumes the actual generated draft path and payload.

### Risk 2: Overfitting to current tests

A “real” draft could still be too shallow if tests only check file existence.

**Mitigation:** add stronger assertions around state updates, payload shape, and failure modes.

### Risk 3: Pulling in too much future roadmap logic

Trying to complete audit/revise/import/startup at the same time would slow delivery.

**Mitigation:** keep this plan explicitly scoped to draft MVP and continuation baseline integrity.

## Open Questions

The execution phase still needs to decide the exact minimum draft inputs/outputs, but that should be resolved during task 2 before implementation begins. It is not a blocker for planning.
