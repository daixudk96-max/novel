# Design: Activate Route A provider-by-env implementation

## Goal

Turn `novel chapter draft` into the first real Route A ingress by replacing placeholder-only drafting with a Novel-owned, env-resolved provider path inside the runtime while keeping the shared chapter lifecycle and all Route B surfaces unchanged.

## Architecture

### Runtime flow
1. `novel chapter draft` stays the public CLI entrypoint.
2. CLI delegates drafting to `novel_runtime.pipeline.drafter.ChapterDrafter`.
3. `ChapterDrafter` resolves Route A runtime dependencies through a narrow `novel_runtime.llm.provider` seam.
4. Draft temperature is computed by `novel_runtime.llm.temperature`, not inline in the drafter.
5. Provider output is normalized back into the existing `ChapterDraft` shape so downstream `settle → postcheck → audit → route → revise → approve` behavior does not change.

### Scope boundary
- In scope: one concrete provider path, env-only config, draft-specific temperature policy, exact fail-fast errors, fake-test-only verification.
- Out of scope: Route B, REST/network-service/MCP surfaces, config files, provider plugins, broad resilience implementation.

## Tech Stack

- Python runtime and CLI modules already in repo
- `pytest` for unit/CLI regression coverage
- Fake providers and env patching for deterministic tests

## File Structure

- Create `novel-runtime/novel_runtime/llm/__init__.py`
- Create `novel-runtime/novel_runtime/llm/provider.py`
- Create `novel-runtime/novel_runtime/llm/temperature.py`
- Modify `novel-runtime/novel_runtime/pipeline/drafter.py`
- Modify `novel-cli/novel_cli/commands/chapter.py`
- Modify `tests/test_drafter.py`
- Modify `tests/test_cli_chapter.py`

## Key Decisions

1. **Route A only**: this slice activates only Novel-internal provider/API-by-env execution from Phase 3 Route A.
2. **Env-only contract**: use only `NOVEL_LLM_PROVIDER`, `NOVEL_LLM_MODEL`, and `NOVEL_LLM_API_KEY`; no flags or config files.
3. **Single-provider seam**: keep one concrete provider behind a fakeable abstraction instead of designing a platform.
4. **Fail fast**: missing or invalid env must surface deterministic CLI-visible errors in plain and JSON modes; no placeholder fallback.
5. **Temperature isolation**: temperature validation and normalization live outside `ChapterDrafter`.
6. **Resilience seam only**: leave room for later resilience work, but do not implement retries, backoff, rate limiting, or Route B contracts here.

## Edge Cases

- `NOVEL_LLM_PROVIDER` missing, unsupported, or inconsistent with required env
- `NOVEL_LLM_MODEL` missing or empty
- `NOVEL_LLM_API_KEY` missing or empty
- Invalid draft temperature input or normalization rules
- Provider exception propagation into exact CLI errors
- Empty provider output while chapter/entity validation must remain deterministic
- JSON mode must preserve existing payload shape even on failure

## Open Questions

- Which exact provider identifier is the single allowed value for this slice?
- Should temperature input remain fully internal for now, or be derived from existing draft defaults only?
- Where should future `llm/resilience.py` hook in without changing the provider contract introduced here?
