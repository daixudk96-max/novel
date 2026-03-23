from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import click
from novel_runtime.state.canonical import CANONICAL_STATE_FILENAME, CanonicalState

CURRENT_PROJECT_FILENAME = ".novel_project_path"
DEFAULT_GENRE = "general"


@click.group(name="project")
def project_group() -> None:
    pass


@project_group.command("init")
@click.argument("name")
@click.option("--genre", default=DEFAULT_GENRE, show_default=True)
@click.option("--json", "json_output", is_flag=True)
def init_project(name: str, genre: str, json_output: bool) -> None:
    current_dir = Path.cwd()
    if _state_path(current_dir).is_file():
        _fail("already inside a novel project", json_output)

    project_dir = current_dir / name
    if project_dir.exists():
        _fail(f"project path already exists: {project_dir}", json_output)

    state = CanonicalState.create_empty(project_name=name, genre=genre)
    state_path = state.save(project_dir)
    _write_current_project_path(project_dir)

    payload = {
        "name": name,
        "genre": genre,
        "path": str(project_dir.resolve()),
        "state_path": str(state_path.resolve()),
    }
    _emit(
        payload, f"Initialized project '{name}' at {project_dir.resolve()}", json_output
    )


@project_group.command("info")
@click.option("--json", "json_output", is_flag=True)
def project_info(json_output: bool) -> None:
    project_dir = _resolve_project_dir()
    state = CanonicalState.load(project_dir)
    payload = {
        "name": state.data["project"]["name"],
        "genre": state.data["project"]["genre"],
        "chapter_count": len(state.data["chapters"]),
        "path": str(project_dir.resolve()),
    }
    text = "\n".join(
        (
            f"Name: {payload['name']}",
            f"Genre: {payload['genre']}",
            f"Chapters: {payload['chapter_count']}",
            f"Path: {payload['path']}",
        )
    )
    _emit(payload, text, json_output)


@project_group.command("open")
@click.argument("path", type=click.Path(path_type=Path))
@click.option("--json", "json_output", is_flag=True)
def open_project(path: Path, json_output: bool) -> None:
    project_dir = path.resolve()
    if not _state_path(project_dir).is_file():
        _fail(f"not a novel project: {project_dir}", json_output)

    _write_current_project_path(project_dir)
    state = CanonicalState.load(project_dir)
    payload = {
        "name": state.data["project"]["name"],
        "genre": state.data["project"]["genre"],
        "chapter_count": len(state.data["chapters"]),
        "path": str(project_dir),
    }
    _emit(payload, f"Opened project '{payload['name']}' at {project_dir}", json_output)


def _resolve_project_dir() -> Path:
    current_dir = Path.cwd()
    if _state_path(current_dir).is_file():
        return current_dir

    marker_path = current_dir / CURRENT_PROJECT_FILENAME
    if marker_path.is_file():
        project_dir = Path(marker_path.read_text(encoding="utf-8").strip()).resolve()
        if _state_path(project_dir).is_file():
            return project_dir

    raise click.ClickException("no novel project selected")


def _write_current_project_path(project_dir: Path) -> None:
    (Path.cwd() / CURRENT_PROJECT_FILENAME).write_text(
        str(project_dir.resolve()), encoding="utf-8"
    )


def _state_path(project_dir: Path) -> Path:
    return project_dir / CANONICAL_STATE_FILENAME


def _emit(payload: Mapping[str, object], text: str, json_output: bool) -> None:
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False))
        return

    click.echo(text)


def _fail(message: str, json_output: bool) -> None:
    if json_output:
        raise click.ClickException(json.dumps({"error": message}, ensure_ascii=False))
    raise click.ClickException(message)


__all__ = ["project_group"]
