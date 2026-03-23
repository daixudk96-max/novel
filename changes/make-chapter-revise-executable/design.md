# Design: Make Chapter Revise Executable

## Goal

Add the confidence router and chapter reviser atoms to the chapter continuation spine so the CLI/runtime proof path can reach `draft → settle → postcheck → audit → route → revise → snapshot`.

## Roadmap Position

This follows `make-chapter-audit-executable`. It does not expand into approve, export, LLM integration, or startup work. The continuation spine remains the P0 workflow.

## Current State

The continuation path now walks `draft → settle → postcheck → audit → snapshot`. Audit emits structured results with `status`, `severity`, `recommended_action`, and `issues`. When audit returns `recommended_action: revise_chapter`, there is no runtime atom to act on that recommendation. The pipeline skips to snapshot regardless.

Existing pipeline modules: `drafter.py`, `settler.py`, `postcheck.py`, `auditor.py`.
Existing CLI commands: `chapter draft`, `chapter settle`, `chapter postcheck`, `chapter audit`.

## Scope

- **In scope:**
  - Runtime confidence router that maps audit results to routing decisions
  - Runtime chapter reviser that produces revised text from audit findings
  - CLI `chapter route` and `chapter revise` commands
  - Tests: contract freeze, runtime proofs, CLI assertions, e2e continuation path
  - Template-based revision (no LLM)

- **Out of scope:**
  - `approve` command
  - LLM-powered revision
  - Re-settle / re-postcheck loop after revision
  - Export, startup, outline

## Architecture

### Confidence Router

The router is a pure function: `AuditResult → RoutingDecision`. It uses deterministic rules based on audit severity and issue counts:

| Audit Status | Severity | Action | Meaning |
|-------------|----------|--------|---------|
| pass | none | `pass` | No issues, proceed to snapshot |
| pass | minor | `pass` | Minor issues only, proceed to snapshot |
| fail | major | `revise` | Major issues, send to reviser for spot-fixes |
| fail | blocker | `rewrite` | Blocker issues, chapter needs full rewrite |
| fail | blocker (3+) | `escalate` | Too many blockers, needs human intervention |

The router returns a `RoutingDecision` dataclass with `action`, `reason`, and the original `audit_result` reference.

### Chapter Reviser

The reviser takes chapter text + audit result + routing decision and produces revised text. In this slice, revision is template-based:

- For each audit issue, the reviser appends a `<!-- REVISION NOTE: {rule} - {message} -->` comment at the end of the chapter text.
- The revised text is returned along with a revision log listing what was addressed.

This is intentionally minimal — the shape of the pipeline matters more than the quality of revision at this stage. Real LLM-powered revision will replace the template logic in a future slice.

The reviser returns a `RevisionResult` dataclass with `chapter`, `revised_text`, `revision_log`, and `issues_addressed`.

### CLI Commands

Both commands follow the established pattern from `chapter audit`:

- `novel chapter route --chapter N --audit-file PATH [--json]`
  - Reads audit result from a JSON file (output of `chapter audit --json`)
  - Invokes router
  - Emits routing decision as plain text or JSON

- `novel chapter revise --chapter N --text-file PATH --audit-file PATH [--json]`
  - Reads chapter text and audit result
  - Invokes router internally, then reviser
  - Emits revised text + revision log as plain text or JSON
  - Writes revised text to `chapters/chapter_N_revised.md`

## Proposed File Changes

### New files:
- `novel-runtime/novel_runtime/pipeline/router.py` — RoutingDecision, ConfidenceRouter
- `novel-runtime/novel_runtime/pipeline/reviser.py` — RevisionResult, ChapterReviser
- `tests/test_router.py` — router contract and logic tests
- `tests/test_reviser.py` — reviser contract and logic tests

### Modified files:
- `novel-cli/novel_cli/commands/chapter.py` — add `route` and `revise` commands
- `tests/test_cli_chapter.py` — CLI tests for route and revise
- `tests/test_cli_e2e.py` — extend e2e path to include route + revise

## Key Decisions

1. **Router is deterministic, no LLM** — Pure severity-based rules. Keeps the atom testable and fast.
2. **Reviser is template-based** — Matches the current drafter pattern. Real revision deferred to LLM slice.
3. **Reviser does NOT mutate state** — Revised text is output-only. Re-settling is a future concern.
4. **Route command reads audit JSON from file** — Enables pipeline composition: `audit --json > audit.json && route --audit-file audit.json`.
5. **Revise command invokes router internally** — The revise command doesn't require a separate route step; it routes and revises in one call for convenience.

## Edge Cases

- Audit result with `pass` status: router returns `pass`, reviser is not invoked (CLI skips revision).
- Audit result with no issues but `fail` status: should not happen given current auditor logic, but router treats it as `pass`.
- Empty chapter text: reviser still processes and returns the text with revision notes appended.
- Malformed audit JSON file: CLI returns non-zero with error message.
- Router returns `escalate`: CLI emits the decision but does NOT invoke reviser (human intervention needed).
- Router returns `rewrite`: CLI emits the decision but does NOT invoke reviser (full rewrite, not spot-fix).

## Risks

- Scope creep toward approve/LLM. Mitigation: tests explicitly assert template-based behavior and defer approve.
- Reviser accidentally mutates state. Mitigation: tests prove no state mutation after revise.
- Router rules need tuning with real data. Mitigation: rules are simple and can be adjusted when LLM audit data arrives.
