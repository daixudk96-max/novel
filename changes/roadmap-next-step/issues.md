# Issues

- Task 1 currently says to update planning/status artifacts before implementation, which conflicts with the plan rule that docs/status should update only after proof is green.
- The retry contract is underspecified: retryable classes, fail-fast classes, retry budget, backoff/jitter policy, and exhausted-retry error shape are not frozen precisely enough.
- The current E2E selector in Task 3 proves nothing because it matches zero tests.
- Task 5 doc-sync scope is too narrow if `architecture-novel-runtime-v1.md` and `changes/reframe-roadmap-api-and-helper-cli/design.md` remain stale.
