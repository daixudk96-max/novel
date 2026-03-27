from __future__ import annotations

from novel_runtime.state.canonical import CanonicalState

ALLOWED_OPERATIONS = [
    "read_project_files",
    "write_text_artifact",
    "write_json_artifact",
    "invoke_published_cli_command",
    "capture_command_receipt",
    "bundle_named_outputs",
]


def first_active_world_entity(state: CanonicalState) -> dict | None:
    for entity in state.data["world"]["entities"]:
        if not isinstance(entity, dict):
            continue
        if entity.get("visibility") != "active":
            continue
        if not isinstance(entity.get("name"), str) or not entity["name"].strip():
            continue
        return entity
    return None


class ChapterGuider:
    def guide(self, state: CanonicalState, chapter_number: int) -> dict[str, object]:
        if type(chapter_number) is not int:
            raise ValueError("chapter_number must be an integer")
        if first_active_world_entity(state) is None:
            raise ValueError(
                f"chapter {chapter_number} guide requires at least one active world entity"
            )

        return {
            "guidance_id": f"guide-chapter-{chapter_number}-route-b-v1",
            "version": "route-b-guidance/v1",
            "workflow_id": "chapter-guided-assistant-v1",
            "chapter": chapter_number,
            "route": "Route B phase 1",
            "allowed_operations": list(ALLOWED_OPERATIONS),
            "required_inputs": [
                {
                    "key": "chapter_number",
                    "source_of_truth": "chapter guide --chapter N",
                    "access": "guidance_metadata",
                },
                {
                    "key": "selected_project",
                    "source_of_truth": "published CLI project context",
                    "access": "guidance_metadata",
                },
            ],
            "required_artifacts": [
                {
                    "key": "prose_artifact",
                    "kind": "text",
                    "required": True,
                    "description": "Chapter prose artifact produced by the assistant",
                },
                {
                    "key": "settlement_artifact",
                    "kind": "json",
                    "required": True,
                    "description": "Assistant-filled settlement JSON created from the emitted template",
                },
                {
                    "key": "assistant_result_manifest",
                    "kind": "json",
                    "required": True,
                    "description": "assistant-result/v1 manifest returned for CLI validation",
                },
            ],
            "command_sequence": [
                {
                    "step_id": "read-chapter-context",
                    "operation": "read_project_files",
                    "inputs": ["chapter_number", "selected_project"],
                    "outputs": ["chapter_context"],
                },
                {
                    "step_id": "write-prose-artifact",
                    "operation": "write_text_artifact",
                    "inputs": ["chapter_context"],
                    "outputs": ["prose_artifact"],
                },
                {
                    "step_id": "write-settlement-artifact",
                    "operation": "write_json_artifact",
                    "inputs": ["prose_artifact"],
                    "outputs": ["settlement_artifact"],
                },
                {
                    "step_id": "bundle-return-artifacts",
                    "operation": "bundle_named_outputs",
                    "inputs": ["prose_artifact", "settlement_artifact"],
                    "outputs": ["assistant_result_manifest"],
                },
            ],
            "validation_gates": [
                {
                    "gate_id": "manifest-matches-upstream-contract",
                    "description": "Return manifest must satisfy assistant-result/v1 exactly",
                },
                {
                    "gate_id": "settlement-file-present",
                    "description": "Settlement JSON must exist as a separate file-backed artifact",
                },
                {
                    "gate_id": "forbidden-paths-not-used",
                    "description": "No returned path may resolve to canonical_state.json or .novel_project_path",
                },
            ],
            "settlement_template": {
                "chapter": chapter_number,
                "prose_path": f"artifacts/chapter-{chapter_number}/chapter-{chapter_number}.md",
                "summary": "",
                "continuity_notes": [],
                "open_questions": [],
            },
            "expected_return_manifest": {
                "manifest_name": "assistant-result-v1",
                "required_reference_field": "guidance_id",
            },
            "next_cli_step": "chapter verify-guided-result",
        }


__all__ = ["ALLOWED_OPERATIONS", "ChapterGuider", "first_active_world_entity"]
