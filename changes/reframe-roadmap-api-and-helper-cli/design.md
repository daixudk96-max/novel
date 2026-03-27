# Readiness Taxonomy: shared core + dual-route chapter ingress

This note freezes the status language for Phase 3 roadmap reporting. It extends the existing command-level vocabulary (`primary-partial`, `secondary-only`, `blocked-by-missing-atom`) with route-scoped readiness labels instead of replacing it.

## Why a second vocabulary layer exists

- `primary-partial`, `secondary-only`, and `blocked-by-missing-atom` still describe the maturity of individual commands or workflow steps.
- The roadmap also needs route-scoped labels for release claims across the shared chapter lifecycle.
- Those route-scoped labels must stay explicit about scope so one route cannot accidentally claim readiness earned by another route.

## Command-level vocabulary stays in force

- `primary-partial`: a valid current machine surface exists, but the broader roadmap capability is still only partially implemented.
- `secondary-only`: callable or visible behavior exists, but it is intentionally outside the primary readiness claim.
- `blocked-by-missing-atom`: the workflow step is known, but the needed public CLI atom is not available yet.

These labels remain useful inside command tables, workflow steps, and CLI contract discussions. They do not answer whether the shared lifecycle or either route is ready.

## Route-scoped readiness vocabulary

### `shared-core ready`

`shared-core ready` means Novel can accept chapter text plus required structured inputs and run the route-neutral lifecycle end to end: `settle → postcheck → audit → route → revise → approve → snapshot`.

It includes shared ownership of:

- canonical state persistence and normalization
- settlement and validation semantics
- audit, routing, revision, approval, and snapshot behavior
- CLI-first machine access to those shared lifecycle steps

It does **not** mean either ingress route is complete. A repo can be `shared-core ready` while Route A is on the provider-backed ingress track and Route B remains phase-scoped.

### `Route A ready`

`Route A ready` means Novel itself can perform the drafting/generation ingress by using env-configured provider settings inside Novel, then hand the result into the shared lifecycle.

This label requires all of the following:

- provider/API-by-env execution inside Novel
- route-local quality/reliability work needed for real drafting
- handoff into the same shared-core lifecycle used by every route

`Route A ready` does **not** imply REST, network service, or MCP scope. It only describes provider/API-by-env execution inside the Novel runtime + CLI boundary.

### `Route B phase 1`

`Route B phase 1` means the guided-assistant route is ready for the first supported contract shape:

- CLI guidance export
- assistant execution of allowed operations
- assistant-filled settlement artifact
- CLI validation/ingestion back into the shared lifecycle

This is the complete Route B phase-1 readiness claim. It does not depend on Route A being ready first.

### `Route B phase 2`

`Route B phase 2` means a later Route B enhancement where Novel can auto-extract or normalize settlement details from assistant-produced prose or related artifacts, reducing the amount of assistant-filled settlement work.

`Route B phase 2` is explicitly not part of `Route B phase 1` readiness.

## Non-overlap rules

1. `shared-core ready` is about the common lifecycle after ingress, not about who produced the draft.
2. `Route A ready` applies only to the Novel-internal provider/API-by-env route.
3. `Route B phase 1` and `Route B phase 2` apply only to the CLI-guided assistant route.
4. Route labels must never be used without the route name and phase/ready qualifier.
5. `chapter draft` provider-backed output is not readiness proof for the shared core, Route B, or universal prose-generation readiness.

## How the vocabularies work together

| Scope | Allowed labels | Example use |
| --- | --- | --- |
| command / step | `primary-partial`, `secondary-only`, `blocked-by-missing-atom` | `chapter draft` is `secondary-only`; `chapter settle` is `primary-partial` |
| shared lifecycle | `shared-core ready` | shared settle/audit/revise/approve/snapshot spine is stable |
| Route A ingress | `Route A ready` | provider/API-by-env drafting inside Novel now has shipped provider + resilience + packaged verification proof |
| Route B ingress | `Route B phase 1`, `Route B phase 2` | guidance + assistant-filled settlement comes before auto-extraction |

## Reporting rules for roadmap and follow-on plans

- Use the command-level labels when discussing individual commands, workflow steps, or contract coverage.
- Use `shared-core ready` only when the common lifecycle is what has been proven.
- Use `Route A ready` only for the Novel-internal provider/API-by-env route.
- Use `Route B phase 1` only for guidance + assistant execution + assistant-filled settlement + CLI validation/ingestion.
- Use `Route B phase 2` only for the later auto-extraction enhancement.
- Never upgrade a readiness claim by pointing to `chapter draft` output alone; Route A ready still means provider-backed ingress plus shared-lifecycle handoff, and it does not include REST, network service, or MCP scope.

## Verification lookup keys

The Task 3 evidence commands use literal grep lookup keys in this repo environment. The keys below are recorded as visible verification support so reviewers can rerun the exact documented checks without reinterpreting the search text.

- `shared-core ready|Route A|Route B phase 1|Route B phase 2`
- `chapter draft|placeholder|not readiness`
