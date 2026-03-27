from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from novel_runtime.state.canonical import CANONICAL_STATE_FILENAME

_ASSISTANT_RESULT_VERSION = "assistant-result/v1"
_CURRENT_PROJECT_FILENAME = ".novel_project_path"
_EXPECTED_FIELDS = {
    "guidance_id",
    "version",
    "chapter",
    "operations_performed",
    "created_files",
    "prose_path",
    "settlement_path",
    "command_receipts",
    "warnings",
    "ready_for_cli_validation",
}
_SETTLEMENT_FIELDS = {
    "chapter",
    "prose_path",
    "summary",
    "continuity_notes",
    "open_questions",
}


@dataclass(frozen=True, slots=True)
class AssistantResultValidation:
    guidance_id: str
    chapter: int
    prose_path: Path
    settlement_path: Path
    command_receipts: list[dict[str, object]]
    warnings: list[str]
    ready_for_cli_validation: bool


class AssistantResultValidator:
    def validate(
        self,
        *,
        chapter_number: int,
        manifest_file: Path,
    ) -> AssistantResultValidation:
        if type(chapter_number) is not int:
            raise ValueError("chapter_number must be an integer")

        manifest = self._load_json_object(manifest_file, "manifest file")
        self._validate_manifest_fields(manifest)

        guidance_id = self._require_non_empty_string(manifest, "guidance_id")
        expected_guidance_id = _expected_guidance_id(chapter_number)
        if guidance_id != expected_guidance_id:
            raise ValueError(
                f"manifest guidance_id '{guidance_id}' does not match expected guidance '{expected_guidance_id}'"
            )

        version = self._require_non_empty_string(manifest, "version")
        if version != _ASSISTANT_RESULT_VERSION:
            raise ValueError(
                f"manifest version '{version}' must be '{_ASSISTANT_RESULT_VERSION}'"
            )

        manifest_chapter = manifest["chapter"]
        if type(manifest_chapter) is not int:
            raise ValueError("manifest chapter must be an integer")
        if manifest_chapter != chapter_number:
            raise ValueError(
                f"manifest chapter '{manifest_chapter}' does not match --chapter '{chapter_number}'"
            )

        operations_performed = self._require_string_list(
            manifest, "operations_performed"
        )
        created_files = self._require_string_list(manifest, "created_files")
        prose_path_raw = self._require_non_empty_string(manifest, "prose_path")
        settlement_path_raw = self._require_non_empty_string(
            manifest, "settlement_path"
        )
        warnings = self._require_string_list(manifest, "warnings")
        ready_for_cli_validation = manifest["ready_for_cli_validation"]
        if not isinstance(ready_for_cli_validation, bool):
            raise ValueError("manifest ready_for_cli_validation must be a boolean")
        if not ready_for_cli_validation:
            raise ValueError("manifest ready_for_cli_validation must be true")

        if prose_path_raw not in created_files:
            raise ValueError("manifest created_files must include prose_path")
        if settlement_path_raw not in created_files:
            raise ValueError("manifest created_files must include settlement_path")

        prose_path = self._resolve_declared_path(prose_path_raw, manifest_file.parent)
        settlement_path = self._resolve_declared_path(
            settlement_path_raw, manifest_file.parent
        )
        forbidden_targets = self._forbidden_targets()
        self._reject_forbidden_path(prose_path, "prose_path", forbidden_targets)
        self._reject_forbidden_path(
            settlement_path, "settlement_path", forbidden_targets
        )
        for index, created_file in enumerate(created_files):
            resolved_created_file = self._resolve_declared_path(
                created_file, manifest_file.parent
            )
            self._reject_forbidden_path(
                resolved_created_file,
                f"created_files[{index}]",
                forbidden_targets,
            )

        if not prose_path.is_file():
            raise ValueError(f"prose_path does not exist: {prose_path}")
        settlement = self._load_json_object(settlement_path, "settlement file")
        self._validate_settlement(settlement, manifest_chapter, prose_path_raw)

        command_receipts = self._validate_command_receipts(
            manifest["command_receipts"],
            operations_performed,
            manifest_file.parent,
        )

        return AssistantResultValidation(
            guidance_id=guidance_id,
            chapter=manifest_chapter,
            prose_path=prose_path,
            settlement_path=settlement_path,
            command_receipts=command_receipts,
            warnings=warnings,
            ready_for_cli_validation=True,
        )

    def _validate_manifest_fields(self, manifest: dict[str, object]) -> None:
        manifest_fields = set(manifest)
        missing = sorted(_EXPECTED_FIELDS - manifest_fields)
        extra = sorted(manifest_fields - _EXPECTED_FIELDS)
        problems: list[str] = []
        if missing:
            problems.append(f"missing field(s): {', '.join(missing)}")
        if extra:
            problems.append(f"unexpected field(s): {', '.join(extra)}")
        if problems:
            raise ValueError(
                f"manifest must use assistant-result/v1 field set exactly: {'; '.join(problems)}"
            )

    def _validate_settlement(
        self, settlement: dict[str, object], chapter_number: int, prose_path: str
    ) -> None:
        missing = sorted(_SETTLEMENT_FIELDS - set(settlement))
        if missing:
            raise ValueError(
                f"settlement file missing required field(s): {', '.join(missing)}"
            )
        if type(settlement["chapter"]) is not int:
            raise ValueError("settlement file field 'chapter' must be an integer")
        if settlement["chapter"] != chapter_number:
            raise ValueError(
                f"settlement file chapter '{settlement['chapter']}' does not match manifest chapter '{chapter_number}'"
            )
        if settlement["prose_path"] != prose_path:
            raise ValueError(
                "settlement file field 'prose_path' must match manifest prose_path"
            )
        if not isinstance(settlement["summary"], str):
            raise ValueError("settlement file field 'summary' must be a string")
        if not isinstance(settlement["continuity_notes"], list):
            raise ValueError(
                "settlement file field 'continuity_notes' must be an array"
            )
        if not isinstance(settlement["open_questions"], list):
            raise ValueError("settlement file field 'open_questions' must be an array")

    def _validate_command_receipts(
        self,
        payload: object,
        operations_performed: list[str],
        base_dir: Path,
    ) -> list[dict[str, object]]:
        if not isinstance(payload, list):
            raise ValueError("manifest command_receipts must be an array")
        if "invoke_published_cli_command" in operations_performed and len(payload) == 0:
            raise ValueError(
                "manifest command_receipts must be non-empty when invoke_published_cli_command was performed"
            )

        receipts: list[dict[str, object]] = []
        for index, receipt in enumerate(payload):
            if not isinstance(receipt, dict):
                raise ValueError(f"command_receipts[{index}] must be an object")

            command = receipt.get("command")
            exit_code = receipt.get("exit_code")
            output_path = receipt.get("output_path")
            if not isinstance(command, str) or not command.strip():
                raise ValueError(
                    f"command_receipts[{index}].command must be a non-empty string"
                )
            if type(exit_code) is not int:
                raise ValueError(
                    f"command_receipts[{index}].exit_code must be an integer"
                )
            if output_path is not None:
                if not isinstance(output_path, str) or not output_path.strip():
                    raise ValueError(
                        f"command_receipts[{index}].output_path must be a non-empty string when provided"
                    )
                self._reject_forbidden_path(
                    self._resolve_declared_path(output_path, base_dir),
                    f"command_receipts[{index}].output_path",
                    self._forbidden_targets(),
                )

            receipts.append(dict(receipt))
        return receipts

    def _load_json_object(self, path: Path, label: str) -> dict[str, object]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid {label} JSON: {exc.msg}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"{label} must decode to a JSON object")
        return payload

    def _require_non_empty_string(self, payload: dict[str, object], field: str) -> str:
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"manifest field '{field}' must be a non-empty string")
        return value

    def _require_string_list(self, payload: dict[str, object], field: str) -> list[str]:
        value = payload[field]
        if not isinstance(value, list):
            raise ValueError(f"manifest field '{field}' must be an array")
        items: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    f"manifest field '{field}' entry {index} must be a non-empty string"
                )
            items.append(item)
        return items

    def _resolve_declared_path(self, declared_path: str, base_dir: Path) -> Path:
        path = Path(declared_path)
        if not path.is_absolute():
            path = base_dir / path
        return path.resolve()

    def _forbidden_targets(self) -> set[Path]:
        workspace_dir = Path.cwd().resolve()
        targets = {workspace_dir / _CURRENT_PROJECT_FILENAME}
        selected_project_dir = self._selected_project_dir(workspace_dir)
        if selected_project_dir is not None:
            targets.add(selected_project_dir / CANONICAL_STATE_FILENAME)
        return {target.resolve(strict=False) for target in targets}

    def _selected_project_dir(self, workspace_dir: Path) -> Path | None:
        current_project_state = workspace_dir / CANONICAL_STATE_FILENAME
        if current_project_state.is_file():
            return workspace_dir

        marker_path = workspace_dir / _CURRENT_PROJECT_FILENAME
        if not marker_path.is_file():
            return None

        project_dir = Path(marker_path.read_text(encoding="utf-8").strip()).resolve()
        if (project_dir / CANONICAL_STATE_FILENAME).is_file():
            return project_dir
        return None

    def _reject_forbidden_path(
        self, resolved_path: Path, field: str, forbidden_targets: set[Path]
    ) -> None:
        if resolved_path in forbidden_targets:
            raise ValueError(
                f"manifest {field} resolves to forbidden path '{resolved_path.name}'"
            )


def _expected_guidance_id(chapter_number: int) -> str:
    return f"guide-chapter-{chapter_number}-route-b-v1"


__all__ = ["AssistantResultValidation", "AssistantResultValidator"]
