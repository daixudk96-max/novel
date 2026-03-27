# Design: Make Chapter Guide Assisted Executable (Route B guided-assistant branch)

## Goal

Turn Route B into a first-class peer branch under the dual-route roadmap: the CLI exports structured guidance, the assistant performs allowed operations and writes artifacts, the assistant returns a manifest plus prose and settlement, and the CLI validates that handoff before the shared lifecycle continues through settle, postcheck, audit, route, revise, approve, and snapshot. The Route B Skill remains orchestration-only.

## Roadmap position and shared-core context

Route B is one of two equal ingress branches. It does not depend on Route A provider/API-by-env execution. After ingress, Route B rejoins the same shared core that already owns canonical state, settlement semantics, audit, routing, revision, approval, and snapshot behavior. Route B therefore adds a guidance/export boundary and a validation boundary, not a separate business core.

## Current state

The accepted roadmap and top-level contracts already define the Route B shape:

- `architecture-novel-runtime-v1.md` names Route B as CLI guidance + assistant execution + CLI validation.
- `helper-guidance-contract.md` freezes the exported guidance artifact and the closed operation set.
- `assistant-result-contract.md` freezes the file-backed manifest and the phase-1 settlement requirement.
- `workflow-spec.md` already states that Route B Skills wrap guidance emission, assistant execution expectations, artifact return, and CLI validation while branching only on published machine fields.

What is missing is the decision-frozen Route B branch artifact set under `changes/make-chapter-guide-assisted-executable/`, aligned to the upstream Route B contracts rather than stale parallel vocabulary.

## Scope

- **In scope**
  - Framing Route B as a peer branch under shared core + Route A + Route B.
  - `chapter guide` as the formal Route B export command.
  - Assistant execution constrained to the accepted allowed operations and host-neutral artifact handling.
  - File-backed assistant-result return via manifest + prose + settlement + optional command receipts.
  - `chapter verify-guided-result` as the CLI validate gate before `chapter settle`.
  - Explicit separation between phase 1 assistant-filled settlement and phase 2 auto-extract work.
  - Route B Skill behavior as orchestration-only over the existing CLI contract.

- **Out of scope**
  - Route A provider/API-by-env work.
  - Network API, REST, or MCP transport.
  - Direct assistant mutation of canonical state.
  - Host-specific branching logic, prose parsing, or hidden repo-state branching.
  - Phase 2 auto-extract implementation.

## Architecture

### 1. Guidance export boundary

`chapter guide` is the Route B ingress command. It emits a structured guidance artifact inside the common `novel-cli-agent/v1` success envelope and keeps the host branch surface at the transport layer:

- top-level `recommended_action = "chapter verify-guided-result"`
- `data.guidance_id = "guide-chapter-{N}-route-b-v1"`
- `data.version = "route-b-guidance/v1"`
- `data.workflow_id = "chapter-guided-assistant-v1"`
- `data.chapter = {N}`
- `data.route = "Route B phase 1"`
- `data.allowed_operations`
- `data.required_inputs`
- `data.required_artifacts`
- `data.command_sequence`
- `data.validation_gates`
- `data.settlement_template`
- `data.expected_return_manifest`
- `data.next_cli_step = "chapter verify-guided-result"`

`next_cli_step` remains guidance-artifact metadata only. Hosts and Skills must not branch on it; they may branch only on published transport fields such as `recommended_action`, `ok`, `error.code`, `retryable`, and `version`.

### 2. Assistant execution boundary

The assistant executes only the allowed operation classes named by the guidance contract:

- `read_project_files`
- `write_text_artifact`
- `write_json_artifact`
- `invoke_published_cli_command`
- `capture_command_receipt`
- `bundle_named_outputs`

Those operations are intentionally file/path/receipt oriented and host-neutral. They do not authorize direct edits to `canonical_state.json`, direct lifecycle mutation, assistant-side approvals, or host-specific side channels.

### 3. Result return boundary

The assistant returns a file-backed `assistant-result/v1` manifest that correlates to `guidance_id` and uses the upstream field set exactly, with no extra top-level `workflow_id` or `route` fields:

- `guidance_id`
- `version`
- `chapter`
- `operations_performed`
- `created_files`
- `prose_path`
- `settlement_path`
- `command_receipts`
- `warnings`
- `ready_for_cli_validation`

Large prose remains outside the manifest. If the assistant invoked published CLI commands, receipts must be present.

### 4. CLI validation and shared-core re-entry

`chapter verify-guided-result` is the Route B validate gate. It checks manifest shape, chapter match, file existence, forbidden resolved paths, settlement JSON shape, and receipt presence. It does not mutate canonical state.

Its transport response keeps the same branch discipline:

- top-level `version = "novel-cli-agent/v1"`
- top-level `recommended_action = "chapter settle"`
- validated artifact paths and warnings live under `data`

Only after validation succeeds does Route B re-enter the existing shared lifecycle:

1. `chapter verify-guided-result`
2. `chapter settle`
3. `chapter postcheck`
4. `chapter audit`
5. `chapter route`
6. `chapter revise`
7. `chapter approve`
8. `snapshot create`

This preserves one shared lifecycle regardless of ingress route.

### 5. Settlement maturity split

#### Phase 1

Route B phase 1 requires the assistant to fill the CLI-emitted settlement template and return it as a separate JSON artifact. This is the accepted readiness target for guided assistant execution.

#### Phase 2

Route B phase 2 is a later child slice where Novel may auto-extract or auto-normalize settlement details from prose. That work is deferred and must not weaken the phase-1 requirement for a settlement file.

### 6. Route B Skill behavior

The Route B Skill is a derived orchestration wrapper over the same CLI contract. It may:

- request `chapter guide`
- surface guidance to the assistant host
- collect manifest, prose, settlement, and receipts
- call the CLI validate gate
- continue with shared-core commands based on published machine fields

It must not:

- invent business rules
- branch on prose, `next_cli_step`, or host-only metadata
- settle, audit, route, revise, or approve on its own
- mutate canonical state directly

## Key decisions

1. Make Route B a peer branch, not a Route A fallback.
2. Keep the loop explicit: guidance export → assistant execution → result return → CLI validate → shared-core continuation.
3. Keep the assistant contract file/path/receipt oriented so hosts differ only in packaging, not meaning.
4. Keep `recommended_action` as the only host-branchable next-step field and keep `next_cli_step` as artifact metadata only.
5. Reuse the upstream `assistant-result/v1` manifest shape exactly instead of inventing a branch-local schema.
6. Keep phase 1 and phase 2 split explicit; auto-extract remains deferred.
7. Keep the Skill orchestration-only so Runtime → CLI contract → workflow/spec stays the truth order.

## Edge cases

- Assistant returns prose without settlement: validation must fail.
- Assistant claims published CLI execution without receipts: validation must fail.
- Manifest chapter or guidance correlation does not match: validation must fail.
- Manifest paths that resolve to `canonical_state.json` or `.novel_project_path`: validation must fail.
- Hosts may render guidance differently, but route branching still cannot depend on plain-text, `next_cli_step`, or host-specific metadata.
- Route B remains valid even when Route A provider work is unfinished.

## Open questions

1. Should phase 2 auto-extract produce a new manifest version or keep `assistant-result/v1` while versioning only the settlement extraction logic?
2. Which minimal normalized artifact fields should `chapter verify-guided-result` surface so downstream settle UX stays concise without hiding file provenance?

## Verification lookup keys

- `route-b-guidance/v1|assistant-result/v1|chapter-guided-assistant-v1|recommended_action|next_cli_step`
- `auto-extract|phase 2|deferred`
