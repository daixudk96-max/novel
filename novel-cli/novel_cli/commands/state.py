from __future__ import annotations

import json
import tempfile

import click
from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.snapshot import SnapshotManager, SnapshotNotFoundError

from novel_cli.commands.project import _emit, _fail, _resolve_project_dir


@click.group(name="state")
def state_group() -> None:
    pass


@state_group.command("show")
@click.option("--json", "json_output", is_flag=True)
def show_state(json_output: bool) -> None:
    state, _ = _load_state()
    payload = {"state": state.data}
    _emit(
        payload,
        json.dumps(state.data, ensure_ascii=False, indent=2, sort_keys=True),
        json_output,
    )


@state_group.command("diff")
@click.option("--snapshot", "snapshot_id", required=True)
@click.option("--json", "json_output", is_flag=True)
def diff_state(snapshot_id: str, json_output: bool) -> None:
    state, manager = _load_state_manager()
    try:
        diff = _diff_state_against_snapshot(manager, state, snapshot_id)
    except SnapshotNotFoundError as exc:
        _fail(str(exc), json_output)
        return

    payload = {"snapshot": {"id": snapshot_id}, "diff": diff}
    _emit(payload, _format_diff_text(diff), json_output)


def _load_state() -> tuple[CanonicalState, SnapshotManager]:
    project_dir = _resolve_project_dir()
    return CanonicalState.load(project_dir), SnapshotManager(project_dir)


def _load_state_manager() -> tuple[CanonicalState, SnapshotManager]:
    return _load_state()


def _diff_state_against_snapshot(
    manager: SnapshotManager, state: CanonicalState, snapshot_id: str
) -> dict:
    snapshot_state = manager.load_snapshot(snapshot_id)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_manager = SnapshotManager(temp_dir)
        before_id = temp_manager.create_snapshot(snapshot_state, label="snapshot")
        after_id = temp_manager.create_snapshot(state, label="current")
        return temp_manager.diff_snapshots(before_id, after_id)


def _format_diff_text(diff: dict) -> str:
    entity_diff = diff["entities"]
    chapter_diff = diff["chapters"]
    return "\n".join(
        (
            f"Entities: +{len(entity_diff['added'])} -{len(entity_diff['removed'])} ~{len(entity_diff['changed'])}",
            f"Chapters: +{len(chapter_diff['added'])} -{len(chapter_diff['removed'])} ~{len(chapter_diff['changed'])}",
        )
    )


__all__ = ["state_group"]
