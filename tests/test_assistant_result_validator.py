from __future__ import annotations

import json
from pathlib import Path

import pytest

from novel_runtime.pipeline.assistant_result_validator import AssistantResultValidator
from novel_runtime.state.canonical import CANONICAL_STATE_FILENAME, CanonicalState


def test_verify_guided_result_accepts_valid_manifest() -> None:
    state = CanonicalState.create_empty("mybook", "fantasy")
    state.save(Path.cwd())
    manifest_path = _write_valid_manifest(chapter_number=1)

    validated = AssistantResultValidator().validate(
        chapter_number=1,
        manifest_file=manifest_path,
    )

    assert validated.guidance_id == "guide-chapter-1-route-b-v1"
    assert validated.chapter == 1
    assert (
        validated.prose_path
        == (Path.cwd() / "artifacts" / "chapter-1" / "chapter-1.md").resolve()
    )
    assert (
        validated.settlement_path
        == (
            Path.cwd() / "artifacts" / "chapter-1" / "chapter-1.settlement.json"
        ).resolve()
    )
    assert validated.command_receipts == []
    assert validated.warnings == []
    assert validated.ready_for_cli_validation is True


def test_verify_guided_result_is_non_mutating() -> None:
    state = CanonicalState.create_empty("mybook", "fantasy")
    state.data["chapters"].append(
        {
            "number": 1,
            "title": "Chapter 1",
            "status": "draft",
            "summary": "Summary.",
            "settled_at": "",
        }
    )
    state.save(Path.cwd())
    manifest_path = _write_valid_manifest(chapter_number=1)
    before_state = json.loads(
        json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
    )
    before_files = _project_files()

    AssistantResultValidator().validate(chapter_number=1, manifest_file=manifest_path)

    after_state = json.loads(
        json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
    )
    assert after_state == before_state
    assert _project_files() == before_files


def test_verify_guided_result_rejects_wrong_version() -> None:
    CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())
    manifest_path = _write_valid_manifest(
        chapter_number=1, version="assistant-result/v2"
    )

    with pytest.raises(ValueError, match="manifest version 'assistant-result/v2'"):
        AssistantResultValidator().validate(
            chapter_number=1, manifest_file=manifest_path
        )


def test_verify_guided_result_rejects_wrong_chapter() -> None:
    CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())
    manifest_path = _write_valid_manifest(
        chapter_number=2,
        guidance_id="guide-chapter-1-route-b-v1",
    )

    with pytest.raises(
        ValueError, match="manifest chapter '2' does not match --chapter '1'"
    ):
        AssistantResultValidator().validate(
            chapter_number=1, manifest_file=manifest_path
        )


def test_verify_guided_result_rejects_missing_receipts_when_cli_used() -> None:
    CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())
    manifest_path = _write_valid_manifest(
        chapter_number=1,
        operations_performed=[
            "read_project_files",
            "invoke_published_cli_command",
            "capture_command_receipt",
            "bundle_named_outputs",
        ],
        command_receipts=[],
    )

    with pytest.raises(
        ValueError,
        match="manifest command_receipts must be non-empty when invoke_published_cli_command was performed",
    ):
        AssistantResultValidator().validate(
            chapter_number=1, manifest_file=manifest_path
        )


def test_verify_guided_result_rejects_canonical_state_path() -> None:
    CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())
    prose_alias = (
        Path("artifacts") / "chapter-1" / ".." / ".." / CANONICAL_STATE_FILENAME
    )
    settlement_path = _write_settlement(
        chapter_number=1, prose_path="artifacts/chapter-1/chapter-1.md"
    )
    manifest_path = _write_manifest(
        {
            "guidance_id": "guide-chapter-1-route-b-v1",
            "version": "assistant-result/v1",
            "chapter": 1,
            "operations_performed": ["read_project_files", "bundle_named_outputs"],
            "created_files": [
                prose_alias.as_posix(),
                settlement_path.as_posix(),
            ],
            "prose_path": prose_alias.as_posix(),
            "settlement_path": settlement_path.as_posix(),
            "command_receipts": [],
            "warnings": [],
            "ready_for_cli_validation": True,
        }
    )

    with pytest.raises(
        ValueError,
        match="manifest prose_path resolves to forbidden path 'canonical_state.json'",
    ):
        AssistantResultValidator().validate(
            chapter_number=1, manifest_file=manifest_path
        )


def test_verify_guided_result_rejects_project_marker_path() -> None:
    CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())
    marker = Path(".novel_project_path")
    marker.write_text(str(Path.cwd()), encoding="utf-8")
    prose_path = _write_prose(chapter_number=1)
    settlement_alias = (
        Path("artifacts") / "chapter-1" / ".." / ".." / ".novel_project_path"
    )
    manifest_path = _write_manifest(
        {
            "guidance_id": "guide-chapter-1-route-b-v1",
            "version": "assistant-result/v1",
            "chapter": 1,
            "operations_performed": ["read_project_files", "bundle_named_outputs"],
            "created_files": [
                prose_path.as_posix(),
                settlement_alias.as_posix(),
            ],
            "prose_path": prose_path.as_posix(),
            "settlement_path": settlement_alias.as_posix(),
            "command_receipts": [],
            "warnings": [],
            "ready_for_cli_validation": True,
        }
    )

    with pytest.raises(
        ValueError,
        match="manifest settlement_path resolves to forbidden path '.novel_project_path'",
    ):
        AssistantResultValidator().validate(
            chapter_number=1, manifest_file=manifest_path
        )


def test_verify_guided_result_allows_same_basename_elsewhere() -> None:
    CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())
    prose_path = _write_prose(chapter_number=1)
    harmless_settlement_path = Path("artifacts") / "chapter-1" / "canonical_state.json"
    harmless_settlement_path.write_text(
        json.dumps(
            {
                "chapter": 1,
                "prose_path": prose_path.as_posix(),
                "summary": "Summary.",
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifest_path = _write_manifest(
        {
            "guidance_id": "guide-chapter-1-route-b-v1",
            "version": "assistant-result/v1",
            "chapter": 1,
            "operations_performed": ["read_project_files", "bundle_named_outputs"],
            "created_files": [
                prose_path.as_posix(),
                harmless_settlement_path.as_posix(),
            ],
            "prose_path": prose_path.as_posix(),
            "settlement_path": harmless_settlement_path.as_posix(),
            "command_receipts": [],
            "warnings": [],
            "ready_for_cli_validation": True,
        }
    )

    validated = AssistantResultValidator().validate(
        chapter_number=1, manifest_file=manifest_path
    )

    assert validated.settlement_path == harmless_settlement_path.resolve()


def _write_valid_manifest(
    *,
    chapter_number: int,
    guidance_id: str | None = None,
    version: str = "assistant-result/v1",
    operations_performed: list[str] | None = None,
    command_receipts: list[dict[str, object]] | None = None,
) -> Path:
    prose_path = _write_prose(chapter_number=chapter_number)
    settlement_path = _write_settlement(
        chapter_number=chapter_number,
        prose_path=prose_path.as_posix(),
    )
    return _write_manifest(
        {
            "guidance_id": guidance_id or f"guide-chapter-{chapter_number}-route-b-v1",
            "version": version,
            "chapter": chapter_number,
            "operations_performed": operations_performed
            or [
                "read_project_files",
                "write_text_artifact",
                "write_json_artifact",
                "bundle_named_outputs",
            ],
            "created_files": [prose_path.as_posix(), settlement_path.as_posix()],
            "prose_path": prose_path.as_posix(),
            "settlement_path": settlement_path.as_posix(),
            "command_receipts": command_receipts or [],
            "warnings": [],
            "ready_for_cli_validation": True,
        }
    )


def _write_manifest(payload: dict[str, object]) -> Path:
    path = Path("assistant-result.json")
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _write_prose(*, chapter_number: int) -> Path:
    path = (
        Path("artifacts") / f"chapter-{chapter_number}" / f"chapter-{chapter_number}.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Chapter prose.", encoding="utf-8")
    return path


def _write_settlement(*, chapter_number: int, prose_path: str) -> Path:
    path = (
        Path("artifacts")
        / f"chapter-{chapter_number}"
        / f"chapter-{chapter_number}.settlement.json"
    )
    path.write_text(
        json.dumps(
            {
                "chapter": chapter_number,
                "prose_path": prose_path,
                "summary": "Summary.",
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _project_files() -> set[str]:
    return {
        path.relative_to(Path.cwd()).as_posix()
        for path in Path.cwd().rglob("*")
        if path.is_file()
    }
