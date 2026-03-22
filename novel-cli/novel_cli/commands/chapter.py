from __future__ import annotations

import json
from pathlib import Path
from typing import Never

import click
from novel_runtime.pipeline.drafter import ChapterDraft, ChapterDrafter
from novel_runtime.pipeline.postcheck import PostcheckRunner
from novel_runtime.pipeline.settler import AlreadySettledError, ChapterSettler
from novel_runtime.state.canonical import CanonicalState

from novel_cli.commands.project import _emit, _fail, _resolve_project_dir


@click.group(name="chapter")
def chapter_group() -> None:
    pass


@chapter_group.command("draft")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option("--json", "json_output", is_flag=True)
def draft_chapter(chapter_number: int, json_output: bool) -> None:
    state, project_dir = _load_state()
    try:
        draft = ChapterDrafter().draft(state, chapter_number)
    except ValueError as exc:
        _raise_fail(str(exc), json_output)

    chapter_path = project_dir / "chapters" / f"chapter_{chapter_number}.md"

    chapter_path.parent.mkdir(parents=True, exist_ok=True)
    chapter_path.write_text(draft.content, encoding="utf-8")
    _upsert_chapter(state, draft)
    state.save(project_dir)

    payload = {
        "chapter": draft.chapter,
        "title": draft.title,
        "status": draft.status,
        "path": str(chapter_path.resolve()),
        "summary": draft.summary,
    }
    _emit(
        payload,
        f"Drafted chapter {chapter_number} at {chapter_path.resolve()}",
        json_output,
    )


@chapter_group.command("settle")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--settlement-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--text-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def settle_chapter(
    chapter_number: int,
    settlement_file: Path,
    text_file: Path,
    json_output: bool,
) -> None:
    state, project_dir = _load_state()
    settlement_data = _load_json_object(settlement_file, "settlement file", json_output)
    chapter_text = _read_text_file(text_file)

    try:
        ChapterSettler().settle(state, chapter_number, chapter_text, settlement_data)
    except (AlreadySettledError, ValueError) as exc:
        _raise_fail(str(exc), json_output)
    else:
        state.save(project_dir)
        chapter = _get_chapter(state, chapter_number)
        assert chapter is not None
        payload = {"chapter": chapter_number, "status": chapter["status"]}
        _emit(payload, f"Settled chapter {chapter_number}", json_output)


@chapter_group.command("postcheck")
@click.option("--chapter", "chapter_number", required=True, type=int)
@click.option(
    "--text-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True)
def postcheck_chapter(chapter_number: int, text_file: Path, json_output: bool) -> None:
    state, _ = _load_state()
    if _get_chapter(state, chapter_number) is None:
        _raise_fail(f"chapter '{chapter_number}' not found", json_output)

    result = PostcheckRunner().run(state, chapter_number, _read_text_file(text_file))
    payload = {
        "chapter": chapter_number,
        "passed": result.passed,
        "issues": [issue.to_dict() for issue in result.issues],
    }
    text = _format_postcheck_text(payload)
    _emit(payload, text, json_output)


def _load_state() -> tuple[CanonicalState, Path]:
    project_dir = _resolve_project_dir()
    return CanonicalState.load(project_dir), project_dir


def _upsert_chapter(state: CanonicalState, draft: ChapterDraft) -> dict[str, object]:
    chapter_number = draft.chapter
    title = draft.title
    status = draft.status
    summary = draft.summary
    chapter = _get_chapter(state, chapter_number)
    if chapter is None:
        chapter = {
            "number": chapter_number,
            "title": title,
            "status": status,
            "summary": summary,
            "settled_at": "",
        }
        state.data["chapters"].append(chapter)
        state.data["chapters"].sort(key=lambda item: item["number"])
        return chapter

    chapter["title"] = title
    chapter["status"] = status
    chapter["summary"] = summary
    chapter["settled_at"] = ""
    return chapter


def _get_chapter(state: CanonicalState, chapter_number: int) -> dict | None:
    for chapter in state.data["chapters"]:
        if chapter["number"] == chapter_number:
            return chapter
    return None


def _load_json_object(path: Path, label: str, json_output: bool) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _raise_fail(f"invalid {label} JSON: {exc.msg}", json_output)

    if not isinstance(payload, dict):
        _raise_fail(f"{label} must decode to a JSON object", json_output)
    return payload


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _format_postcheck_text(payload: dict[str, object]) -> str:
    issues = payload["issues"]
    assert isinstance(issues, list)
    lines = [
        f"Chapter: {payload['chapter']}",
        f"Passed: {'yes' if payload['passed'] else 'no'}",
    ]
    if not issues:
        lines.append("Issues: none")
        return "\n".join(lines)

    lines.append("Issues:")
    for issue in issues:
        assert isinstance(issue, dict)
        lines.append(f"- {issue['rule']} | {issue['severity']} | {issue['message']}")
    return "\n".join(lines)


def _raise_fail(message: str, json_output: bool) -> Never:
    _fail(message, json_output)
    raise AssertionError("unreachable")


__all__ = ["chapter_group"]
