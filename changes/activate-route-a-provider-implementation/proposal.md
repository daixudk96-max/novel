# Proposal: Activate Route A provider-by-env implementation

## Problem Statement

The dual-route roadmap is now frozen, but Route A still stops at placeholder chapter drafting. `novel chapter draft` writes deterministic scaffold text instead of calling a real provider through a Novel-owned runtime path, so the shared chapter lifecycle has no genuine Route A ingress yet.

## Proposed Solution

Activate the next Route A implementation slice only. Introduce a narrow env-driven provider/config seam inside `novel_runtime`, add a draft-specific temperature policy, refactor `ChapterDrafter` to consume that seam, and wire `novel chapter draft` to the new runtime behavior without changing any downstream shared-core commands.

### Locked decisions

- **Scope**: Route A only; no Route B work in this slice.
- **Provider model**: one concrete provider behind a narrow abstraction; no provider platform/plugin system.
- **Config source**: env-only for this slice. No new CLI flags, config files, REST surface, MCP surface, or network service.
- **Failure mode**: fail fast with exact CLI-visible errors when provider env is missing/invalid. Do not silently fall back to placeholder generation.
- **Testing**: fake providers only; no live network and no secret-dependent CI tests.
- **Resilience**: if needed, only leave a narrow seam/interface; do not implement retries/backoff/rate-limit orchestration in this slice.
- **Skill boundary**: Route A skill remains orchestration-only and does not own settlement, approval, or hidden business logic.

## Success Criteria

- `novel chapter draft` reaches Route A through runtime provider/config resolution rather than hardcoded placeholder-only behavior.
- The provider path is env-driven via explicit variables and is fully testable with fakes.
- Temperature policy is explicit, validated, and separate from `ChapterDrafter` logic.
- Missing/invalid Route A env produces deterministic exact errors in both plain and JSON CLI modes.
- Existing `settle → postcheck → audit → route → revise → approve` behavior remains unchanged.

## Risks

- Scope drift into broad resilience, multi-provider support, config-file support, or Route B work.
- Partial wiring where tests mock too high in the stack and miss real CLI/runtime integration defects.
- Ambiguous error UX if env parsing and provider selection rules are not fixed up front.

## Alternatives Considered

### Keep placeholder fallback when env is absent

Rejected. That would blur Route A readiness and hide operator/config errors.

### Implement Route B first because it is contract-ready

Rejected for the next slice. Route B planning is complete, but Route A has stronger existing CLI/runtime/test footholds and is faster to turn into the first real ingress.

### Build full resilience now

Rejected. The roadmap allows resilience later, but this slice should first prove the minimal provider-by-env path.
