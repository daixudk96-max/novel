# Proposal: Make Chapter Guide Assisted Executable

## Problem Statement

Route B is already accepted in the roadmap as a first-class ingress, but the current repo still lacks its executable command surface. Shared core is already present, Route A is partial-but-real in code, and Route B remains the first clearly unfinished branch: there is still no shipped `chapter guide`, no shipped `chapter verify-guided-result`, and no route-neutral guided re-entry into `chapter settle`.

The branch docs also drift from the upstream Route B contracts. They currently mix stale Route B vocabulary with the frozen `route-b-guidance/v1`, and they describe a manifest shape that no longer matches the upstream `assistant-result/v1` contract. That means the next branch is still Route B, but it needs a tighter, decision-complete execution plan before implementation starts.

## Roadmap position

Phase 3 is now one shared lifecycle with two ingress routes:

- **Shared core** already owns `settle → postcheck → audit → route → revise → approve → snapshot`.
- **Route A** is Novel-owned provider/API-by-env drafting and is already partially real in repo code.
- **Route B** is the CLI-guided assistant path: export structured guidance, let the assistant perform only allowed file/path/receipt operations, validate the returned manifest, then continue through the same shared core.

This proposal covers **Route B phase 1 only**.

## Proposed solution

1. Freeze Route B branch docs and fixtures against the upstream contracts in `changes/reframe-roadmap-api-and-helper-cli/`.
2. Ship `chapter guide` as a non-mutating export-class command under the `novel-cli-agent/v1` transport envelope and return top-level `recommended_action = "chapter verify-guided-result"`.
3. Ship `chapter verify-guided-result` as a non-mutating validation/probe gate for the upstream `assistant-result/v1` manifest and return top-level `recommended_action = "chapter settle"`.
4. Keep `next_cli_step = "chapter verify-guided-result"` inside the guidance artifact only as metadata; hosts and Skills must branch only on published top-level machine fields such as `recommended_action`.
5. Make `chapter settle` route-neutral by bootstrapping the missing chapter row in-memory when Route B re-enters without a prior `chapter draft`.
6. Prove the full provider-free Route B loop through `guide → verify-guided-result → settle → postcheck → audit → route → revise → approve → snapshot`.
7. Sync taxonomy / contract / workflow / roadmap docs only after behavior and tests are green.

## Frozen decisions

- CLI transport version for the two new commands stays `novel-cli-agent/v1`.
- Guidance artifact version is `route-b-guidance/v1`.
- Guidance route label is `Route B phase 1`.
- Guidance workflow id is `chapter-guided-assistant-v1`.
- Deterministic guidance id is `guide-chapter-{N}-route-b-v1`.
- Assistant return manifest uses the upstream `assistant-result/v1` field set exactly and does not add `workflow_id` or `route`.
- `recommended_action` is the only host-branchable next-step field.
- `next_cli_step` remains artifact metadata inside the guidance payload only.
- Route B phase 1 requires assistant-filled settlement JSON; Phase 2 auto-extract remains deferred.

## Success criteria

- Route B is executable from `chapter guide` without any Route A/provider dependency.
- Validation rejects malformed, incomplete, or forbidden assistant artifacts before canonical state changes.
- Guided ingress can call `chapter settle` without a prior draft row and still preserve shared-core invariants.
- Automated tests prove the full Route B loop with LLM env vars unset.
- Repo docs stop describing Route B as hypothetical and stop using stale Route B contract names.

## Scope boundaries

### In scope
- Route B phase-1 command surface and validation boundary
- guided re-entry into the existing shared lifecycle
- Route B branch docs / fixtures / taxonomy / workflow / roadmap sync

### Out of scope
- Route A expansion or provider hardening
- Phase 2 auto-extract
- REST / MCP / network-service transport
- full CLI-wide envelope migration
- host-specific branching logic

## Risks and mitigations

### Risk 1: Route B contract drift continues
**Mitigation:** Freeze Route B branch docs and fixtures first, align them to `route-b-guidance/v1` and `assistant-result/v1`, and keep `recommended_action` as the only branchable next-step field before runtime work starts.

### Risk 2: guided ingress weakens shared-core safety
**Mitigation:** Keep `chapter settle` as the first mutation gate, bootstrap the missing row in-memory only, and require no-partial-mutation tests.

### Risk 3: scope expands into adjacent roadmap work
**Mitigation:** Keep Route B phase 1 limited to guidance export, assistant-result validation, route-neutral settle bootstrap, end-to-end proof, and final doc sync.
