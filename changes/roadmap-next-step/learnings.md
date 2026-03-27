# Learnings

- Current Route A code path is narrow: `novel_cli.commands.chapter -> ChapterDrafter -> novel_runtime.llm.provider`.
- `novel_runtime/llm/resilience.py` does not exist yet, so the roadmap gap is real rather than already implemented.
- `tests/test_drafter.py -k "resilience or retry or rate_limit or provider"` and `tests/test_cli_chapter.py -k "draft and (retry or rate_limit or provider)"` each currently select 7 tests.
- `tests/test_cli_e2e.py -k "chapter and draft"` currently selects 0 tests, so the existing Task 3 QA command is a false-confidence gap.
- `changes/reframe-roadmap-api-and-helper-cli/design.md` still describes `chapter draft` as placeholder / Route A partial evidence, so Task 5 must likely update more than `route-matrix.md`.
- OpenAI Python already retries connection errors, timeouts, 408, 409, 429, and >=500 with exponential backoff + jitter; repo plan must define whether Novel wraps, constrains, or disables SDK retries to keep behavior deterministic.
