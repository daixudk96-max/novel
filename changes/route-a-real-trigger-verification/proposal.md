# Draft: Route A real trigger verification

## Requirements (confirmed)
- [request]: 指定一个真实验证计划
- [target]: Route A `novel chapter draft` implementation that was just split into atomic commits

## Technical Decisions
- [verification focus]: Validate real CLI-triggered behavior for Route A rather than add more unit-test coverage
- [baseline]: Reuse the finished Route A slice as the implementation under test
- [plan shape]: Produce one dedicated verification plan under `changes/route-a-real-trigger-verification/`
- [boundary]: Keep verification inside the current Route A no-live-network constraint; use real CLI paths plus fake provider seams instead of live OpenAI calls

## Research Findings
- [changes/activate-route-a-provider-implementation/tasks.md:13-19]: Route A scope is env-only, single-provider, fail-fast, and explicitly says fake-provider tests only with no live network
- [changes/activate-route-a-provider-implementation/tasks.md:64-69]: Existing Definition of Done already covers targeted pytest and exact CLI error behavior
- [changes/activate-route-a-provider-implementation/tasks.md:308-312]: Final verification wave is already marked approved
- [changes/add-real-trigger-verification-plan/tasks.md:1-220]: Repo already has a pattern for dedicated real-trigger verification plans that separate environment setup, scenario design, and execution records

## Open Questions
- None

## Scope Boundaries
- INCLUDE: real CLI invocation paths, env setup, success/failure trigger matrix, evidence capture, exact observable outcomes
- EXCLUDE: code changes to runtime/CLI, live provider calls, Route B coverage, MCP/REST expansion, automatic execution of the verification itself
