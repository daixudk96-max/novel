from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from novel_runtime.state.schema import SchemaValidationError, validate_state

CANONICAL_STATE_FILENAME = "canonical_state.json"
_LOCK_SUFFIX = ".lock"


@dataclass(slots=True)
class CanonicalState:
    data: dict

    @classmethod
    def create_empty(cls, project_name: str, genre: str) -> CanonicalState:
        state = {
            "version": 1,
            "project": {
                "name": project_name,
                "genre": genre,
                "created_at": datetime.now(UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
            },
            "world": {
                "entities": [],
                "relationships": [],
            },
            "timeline": {
                "current_chapter": 0,
                "events": [],
            },
            "foreshadows": [],
            "chapters": [],
        }
        validate_state(state)
        return cls(data=state)

    @classmethod
    def load(cls, path: str | Path) -> CanonicalState:
        state_path = _resolve_state_path(path)
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        return cls(data=validate_state(payload))

    def save(self, path: str | Path) -> Path:
        state_path = _resolve_state_path(path)
        payload = validate_state(deepcopy(self.data))
        state_path.parent.mkdir(parents=True, exist_ok=True)

        with _FileLock(state_path.with_name(f"{state_path.name}{_LOCK_SUFFIX}")):
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=state_path.parent,
                prefix=f"{state_path.stem}-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)

            try:
                os.replace(temp_path, state_path)
            except Exception:
                temp_path.unlink(missing_ok=True)
                raise

        return state_path


def _resolve_state_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.name == CANONICAL_STATE_FILENAME:
        return candidate
    return candidate / CANONICAL_STATE_FILENAME


class _FileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle = None

    def __enter__(self) -> _FileLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self.path, "a+b")
        _lock_file(self._handle)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._handle is None:
            return

        try:
            _unlock_file(self._handle)
        finally:
            self._handle.close()


if os.name == "nt":
    import msvcrt

    def _lock_file(handle) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(handle) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


else:
    import fcntl

    def _lock_file(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    def _unlock_file(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


__all__ = ["CANONICAL_STATE_FILENAME", "CanonicalState", "SchemaValidationError"]
