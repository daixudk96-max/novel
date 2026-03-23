from __future__ import annotations

import click
from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.snapshot import SnapshotManager, SnapshotNotFoundError

from novel_cli.commands.project import _emit, _fail, _resolve_project_dir
from novel_cli.commands.state import _format_diff_text


@click.group(name="snapshot")
def snapshot_group() -> None:
    pass


@snapshot_group.command("create")
@click.option("--label")
@click.option("--json", "json_output", is_flag=True)
def create_snapshot(label: str | None, json_output: bool) -> None:
    state, manager = _load_state_manager()
    snapshot_id = manager.create_snapshot(state, label=label)
    snapshot = _get_snapshot(manager, snapshot_id)
    payload = {"snapshot": snapshot}
    _emit(payload, f"Created snapshot '{snapshot_id}'", json_output)


@snapshot_group.command("list")
@click.option("--json", "json_output", is_flag=True)
def list_snapshots(json_output: bool) -> None:
    _, manager = _load_state_manager()
    snapshots = manager.list_snapshots()
    payload = {"count": len(snapshots), "snapshots": snapshots}
    if snapshots:
        text = "\n".join(
            f"{item['id']} | {item['timestamp']} | {item['label'] or '-'} | chapter {item['chapter'] if item['chapter'] is not None else '-'}"
            for item in snapshots
        )
    else:
        text = "No snapshots found"
    _emit(payload, text, json_output)


@snapshot_group.command("diff")
@click.argument("id_a")
@click.argument("id_b")
@click.option("--json", "json_output", is_flag=True)
def diff_snapshots(id_a: str, id_b: str, json_output: bool) -> None:
    _, manager = _load_state_manager()
    try:
        diff = manager.diff_snapshots(id_a, id_b)
    except SnapshotNotFoundError as exc:
        _fail(str(exc), json_output)
        return

    payload = {"snapshots": {"before": id_a, "after": id_b}, "diff": diff}
    _emit(payload, _format_diff_text(diff), json_output)


@snapshot_group.command("rollback")
@click.argument("snapshot_id")
@click.option("--json", "json_output", is_flag=True)
def rollback_snapshot(snapshot_id: str, json_output: bool) -> None:
    _, manager = _load_state_manager()
    try:
        restored = manager.rollback(snapshot_id)
    except SnapshotNotFoundError as exc:
        _fail(str(exc), json_output)
        return

    payload = {"snapshot": {"id": snapshot_id}, "state": restored.data}
    _emit(payload, f"Rolled back to snapshot '{snapshot_id}'", json_output)


def _load_state_manager() -> tuple[CanonicalState, SnapshotManager]:
    project_dir = _resolve_project_dir()
    return CanonicalState.load(project_dir), SnapshotManager(project_dir)


def _get_snapshot(manager: SnapshotManager, snapshot_id: str) -> dict:
    for item in manager.list_snapshots():
        if item["id"] == snapshot_id:
            return item
    return {"id": snapshot_id, "timestamp": None, "label": None, "chapter": None}


__all__ = ["snapshot_group"]
