# Proposal: Make Chapter Continuation Executable

## Problem Statement

`changes/agent-callable-novel-cli` finished the roadmap foundation step: the agent-facing CLI/Skill contract is now stable, host-neutral, and verified. The next roadmap bottleneck is no longer packaging or contract shape. It is that the highest-priority business workflow, `章节续写流程`, is still only partially real in the Python runtime/CLI stack.

Today the repo already has:

- `project` / `world` / `state` / `snapshot` CLI atoms
- `chapter settle`
- `chapter postcheck`
- `chapter draft`, but only as deterministic placeholder scaffolding

It still lacks the minimum real continuation behavior needed for an agent-safe chapter loop. As a result, the roadmap’s continuation workflow remains blocked even though the invocation contract is ready.

## Proposed Solution

Create a narrow follow-on execution change that turns the current chapter continuation path into a real MVP, centered on replacing the placeholder-only `chapter draft` path with a real runtime-backed draft flow while preserving the existing settle/postcheck/snapshot spine.

This change will:

1. lock the current continuation baseline with targeted regression tests,
2. define a real `chapter draft` contract and its minimal required inputs/outputs,
3. implement the smallest real draft runtime path that fits the existing Python CLI/runtime architecture,
4. prove the resulting continuation slice through CLI, runtime, and end-to-end tests.

This change will not attempt to complete the entire roadmap continuation epic in one shot. It is explicitly the MVP slice of that roadmap item.

## Why This Next

- Roadmap priority: `章节续写流程` is P0, while `新书启动流程` is P1.
- Repo readiness: continuation already has Python CLI/runtime/test coverage; startup still lacks outline/approve atoms in Python.
- Dependency order: making `chapter draft` real creates the first honest continuation loop and reduces later rework for audit/revise routing.

## Success Criteria

- `chapter draft` is no longer placeholder-only.
- The continuation slice can be exercised as a real agent-callable CLI workflow: draft -> settle -> postcheck -> snapshot.
- Existing continuation commands keep passing their regression tests.
- New draft behavior is proven by runtime tests, CLI tests, and an end-to-end CLI path.
- No host-specific logic, REPL-only behavior, or prose-only parsing is added.

## Risk Assessment

### Risk 1: Scope expansion into the full continuation epic

Adding audit/revise, approval, export, and startup concerns in the same change would turn a narrow next step into a large multi-epic implementation.

**Mitigation:** keep this change focused on the chapter-draft MVP and only touch the adjacent continuation spine as needed for real draft execution.

### Risk 2: Fake “real draft” that is just a richer placeholder

Replacing one placeholder with a slightly more decorative placeholder would still fail the roadmap intent.

**Mitigation:** define concrete runtime inputs, deterministic CLI/runtime acceptance tests, and failure-path coverage before implementation.

### Risk 3: Breaking the existing settle/postcheck/snapshot path

The draft flow feeds the rest of the continuation chain.

**Mitigation:** first lock the current baseline and rerun targeted regression + e2e tests after every implementation step.

## Alternatives Considered

### Alternative A — Start with new-book startup

Rejected for now. Startup still lacks outline and approve atoms in the Python stack, so it would force broader greenfield work before producing a complete vertical slice.

### Alternative B — Implement audit/revise before real draft

Rejected for now. The workflow still needs a real draft source before downstream audit/revise semantics become useful in agent execution.

### Alternative C — Keep improving docs/contracts first

Rejected. The foundation step is already complete and verified. More contract work would delay the next roadmap bottleneck instead of removing it.
