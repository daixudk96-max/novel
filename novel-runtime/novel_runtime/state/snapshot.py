from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.schema import validate_state

SNAPSHOTS_DIRNAME = "snapshots"


class SnapshotNotFoundError(FileNotFoundError):
    pass


@dataclass(slots=True)
class SnapshotManager:
    project_path: Path

    def __post_init__(self) -> None:
        self.project_path = Path(self.project_path)

    def create_snapshot(self, state: CanonicalState, label: str | None = None) -> str:
        snapshot_state = validate_state(deepcopy(state.data))
        timestamp = _utcnow()
        snapshot_id = self._allocate_snapshot_id(timestamp)
        payload = {
            "id": snapshot_id,
            "timestamp": timestamp,
            "label": label,
            "chapter": _extract_chapter(snapshot_state),
            "state": snapshot_state,
        }
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)
        self._snapshot_path(snapshot_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return snapshot_id

    def list_snapshots(self) -> list[dict]:
        if not self._snapshots_dir.exists():
            return []

        snapshots = []
        for path in sorted(self._snapshots_dir.glob("*.json")):
            payload = self._read_snapshot_payload(path.stem)
            snapshots.append(
                {
                    "id": payload["id"],
                    "timestamp": payload["timestamp"],
                    "label": payload.get("label"),
                    "chapter": payload.get("chapter"),
                }
            )
        return snapshots

    def load_snapshot(self, snapshot_id: str) -> CanonicalState:
        payload = self._read_snapshot_payload(snapshot_id)
        return CanonicalState(data=deepcopy(payload["state"]))

    def diff_snapshots(self, id_a: str, id_b: str) -> dict:
        before = self.load_snapshot(id_a).data
        after = self.load_snapshot(id_b).data
        return {
            "entities": _diff_collection(
                before["world"]["entities"],
                after["world"]["entities"],
                key="id",
            ),
            "chapters": _diff_collection(
                before["chapters"], after["chapters"], key="number"
            ),
        }

    def rollback(self, snapshot_id: str) -> CanonicalState:
        restored = self.load_snapshot(snapshot_id)
        restored.save(self.project_path)
        return restored

    @property
    def _snapshots_dir(self) -> Path:
        return self.project_path / SNAPSHOTS_DIRNAME

    def _allocate_snapshot_id(self, timestamp: str) -> str:
        candidate = _snapshot_id_from_timestamp(timestamp)
        snapshot_id = candidate
        suffix = 1
        while self._snapshot_path(snapshot_id).exists():
            snapshot_id = f"{candidate}-{suffix:02d}"
            suffix += 1
        return snapshot_id

    def _read_snapshot_payload(self, snapshot_id: str) -> dict:
        path = self._snapshot_path(snapshot_id)
        if not path.exists():
            raise SnapshotNotFoundError(f"snapshot '{snapshot_id}' was not found")

        payload = json.loads(path.read_text(encoding="utf-8"))
        state = _extract_snapshot_state(payload)
        return {
            "id": payload.get("id", snapshot_id),
            "timestamp": payload.get(
                "timestamp", _timestamp_from_snapshot_id(snapshot_id)
            ),
            "label": payload.get("label"),
            "chapter": payload.get("chapter", _extract_chapter(state)),
            "state": state,
        }

    def _snapshot_path(self, snapshot_id: str) -> Path:
        return self._snapshots_dir / f"{snapshot_id}.json"


def _diff_collection(before: list[dict], after: list[dict], key: str) -> dict:
    before_map = {item[key]: deepcopy(item) for item in before}
    after_map = {item[key]: deepcopy(item) for item in after}

    added_keys = sorted(set(after_map) - set(before_map))
    removed_keys = sorted(set(before_map) - set(after_map))
    changed_keys = sorted(
        item_key
        for item_key in set(before_map).intersection(after_map)
        if before_map[item_key] != after_map[item_key]
    )

    return {
        "added": [after_map[item_key] for item_key in added_keys],
        "removed": [before_map[item_key] for item_key in removed_keys],
        "changed": [
            {
                key: item_key,
                "before": before_map[item_key],
                "after": after_map[item_key],
            }
            for item_key in changed_keys
        ],
    }


def _extract_snapshot_state(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("snapshot payload must be a dict")
    if "state" in payload:
        return validate_state(deepcopy(payload["state"]))
    return validate_state(deepcopy(payload))


def _extract_chapter(state: dict) -> int | None:
    current_chapter = state.get("timeline", {}).get("current_chapter")
    if isinstance(current_chapter, int) and current_chapter > 0:
        return current_chapter

    chapters = state.get("chapters", [])
    if chapters:
        return max(
            chapter["number"]
            for chapter in chapters
            if isinstance(chapter.get("number"), int)
        )
    return None


def _timestamp_from_snapshot_id(snapshot_id: str) -> str | None:
    raw = snapshot_id.split("-", 1)[0]
    if len(raw) != 22 or not raw.endswith("Z"):
        return None
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}T{raw[9:11]}:{raw[11:13]}:{raw[13:15]}.{raw[15:21]}Z"


def _snapshot_id_from_timestamp(timestamp: str) -> str:
    moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return moment.strftime("%Y%m%dT%H%M%S%fZ")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


__all__ = ["SNAPSHOTS_DIRNAME", "SnapshotManager", "SnapshotNotFoundError"]
