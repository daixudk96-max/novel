from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.schema import validate_state
from novel_runtime.state.world_model import WorldModel

_SETTLEMENT_KEYS = {
    "new_entities",
    "updated_entities",
    "new_relationships",
    "events",
    "foreshadow_updates",
}

_GUIDED_SETTLEMENT_METADATA_KEYS = {
    "chapter",
    "prose_path",
    "summary",
    "continuity_notes",
    "open_questions",
}


class AlreadySettledError(ValueError):
    pass


class ChapterSettler:
    def settle(
        self,
        state: CanonicalState,
        chapter_number: int,
        chapter_text: str,
        settlement_data: dict,
    ) -> CanonicalState:
        if type(chapter_number) is not int:
            raise ValueError("chapter_number must be an integer")
        if not isinstance(chapter_text, str):
            raise ValueError("chapter_text must be a string")
        if not isinstance(settlement_data, dict):
            raise ValueError("settlement_data must be a dict")

        working_state = CanonicalState(data=deepcopy(state.data))
        chapter = self._get_or_bootstrap_chapter(working_state, chapter_number)
        if chapter["status"] != "draft":
            raise AlreadySettledError(f"chapter '{chapter_number}' is already settled")

        payload = self._normalize_settlement_data(settlement_data)
        self._validate_settlement_data(working_state, payload)
        self._apply_settlement_data(working_state, chapter, payload)
        validate_state(working_state.data)
        state.data = working_state.data
        return state

    def _get_or_bootstrap_chapter(
        self, state: CanonicalState, chapter_number: int
    ) -> dict:
        try:
            return self._get_chapter(state, chapter_number)
        except ValueError:
            chapter = {
                "number": chapter_number,
                "title": f"Chapter {chapter_number}",
                "status": "draft",
                "summary": "",
                "settled_at": "",
            }
            state.data["chapters"].append(chapter)
            state.data["chapters"].sort(key=lambda item: item["number"])
            return chapter

    def _get_chapter(self, state: CanonicalState, chapter_number: int) -> dict:
        for chapter in state.data["chapters"]:
            if chapter["number"] == chapter_number:
                return chapter
        raise ValueError(f"chapter '{chapter_number}' not found")

    def _normalize_settlement_data(self, settlement_data: dict) -> dict:
        allowed_keys = _SETTLEMENT_KEYS | _GUIDED_SETTLEMENT_METADATA_KEYS
        unknown_keys = sorted(set(settlement_data) - allowed_keys)
        if unknown_keys:
            raise ValueError(f"unknown settlement fields: {', '.join(unknown_keys)}")

        payload = {
            key: deepcopy(settlement_data.get(key, [])) for key in _SETTLEMENT_KEYS
        }
        for key, value in payload.items():
            if not isinstance(value, list):
                raise ValueError(f"settlement_data.{key} must be a list")
        return payload

    def _validate_settlement_data(
        self, state: CanonicalState, settlement_data: dict
    ) -> None:
        world = WorldModel(state)
        existing_ids = {entity["id"] for entity in state.data["world"]["entities"]}
        existing_names = {entity["name"] for entity in state.data["world"]["entities"]}
        pending_ids: set[str] = set()
        pending_names: set[str] = set()

        for index, entity in enumerate(settlement_data["new_entities"]):
            path = f"settlement_data.new_entities[{index}]"
            self._validate_new_entity(
                entity, path, existing_ids, existing_names, pending_ids, pending_names
            )
            pending_ids.add(entity["id"])
            pending_names.add(entity["name"])

        available_ids = existing_ids | pending_ids

        for index, entity_update in enumerate(settlement_data["updated_entities"]):
            path = f"settlement_data.updated_entities[{index}]"
            self._validate_entity_update(
                state, world, entity_update, path, existing_names, pending_names
            )

        for index, relationship in enumerate(settlement_data["new_relationships"]):
            path = f"settlement_data.new_relationships[{index}]"
            self._validate_relationship(relationship, path, available_ids)

        for index, event in enumerate(settlement_data["events"]):
            path = f"settlement_data.events[{index}]"
            self._validate_event(event, path, available_ids)

    def _validate_new_entity(
        self,
        entity: object,
        path: str,
        existing_ids: set[str],
        existing_names: set[str],
        pending_ids: set[str],
        pending_names: set[str],
    ) -> None:
        if not isinstance(entity, dict):
            raise ValueError(f"{path} must be a dict")
        required = {"id", "name", "type", "attributes", "visibility"}
        missing = sorted(required - set(entity))
        if missing:
            raise ValueError(f"{path} missing required field(s): {', '.join(missing)}")
        if entity["id"] in existing_ids or entity["id"] in pending_ids:
            raise ValueError(f"{path}.id '{entity['id']}' already exists")
        if entity["name"] in existing_names or entity["name"] in pending_names:
            raise ValueError(f"{path}.name '{entity['name']}' already exists")

        trial_state = {
            "version": 1,
            "project": {"name": "", "genre": "", "created_at": ""},
            "world": {"entities": [deepcopy(entity)], "relationships": []},
            "timeline": {"current_chapter": 0, "events": []},
            "foreshadows": [],
            "chapters": [],
        }
        validate_state(trial_state)

    def _validate_entity_update(
        self,
        state: CanonicalState,
        world: WorldModel,
        entity_update: object,
        path: str,
        existing_names: set[str],
        pending_names: set[str],
    ) -> None:
        if not isinstance(entity_update, dict):
            raise ValueError(f"{path} must be a dict")
        if "id" not in entity_update or not isinstance(entity_update["id"], str):
            raise ValueError(f"{path}.id must be a string")
        if world.get_entity(entity_update["id"]) is None:
            raise ValueError(f"entity '{entity_update['id']}' not found")

        allowed_fields = {"id", "name", "type", "attributes", "visibility"}
        unknown_fields = sorted(set(entity_update) - allowed_fields)
        if unknown_fields:
            raise ValueError(f"{path} has unknown fields: {', '.join(unknown_fields)}")

        if "name" in entity_update:
            name = entity_update["name"]
            current = world.get_entity(entity_update["id"])
            if current is None:
                raise ValueError(f"entity '{entity_update['id']}' not found")
            if name != current["name"] and (
                name in existing_names or name in pending_names
            ):
                raise ValueError(f"{path}.name '{name}' already exists")

        trial_state = CanonicalState(data=deepcopy(state.data))
        WorldModel(trial_state).update_entity(
            entity_update["id"], **self._update_fields(entity_update)
        )
        validate_state(trial_state.data)

    def _validate_relationship(
        self, relationship: object, path: str, available_ids: set[str]
    ) -> None:
        if not isinstance(relationship, dict):
            raise ValueError(f"{path} must be a dict")
        required = {"source", "target", "type", "since_chapter"}
        missing = sorted(required - set(relationship))
        if missing:
            raise ValueError(f"{path} missing required field(s): {', '.join(missing)}")
        for field in ("source", "target", "type"):
            if not isinstance(relationship[field], str):
                raise ValueError(f"{path}.{field} must be a string")
        if type(relationship["since_chapter"]) is not int:
            raise ValueError(f"{path}.since_chapter must be an integer")
        for field in ("source", "target"):
            if relationship[field] not in available_ids:
                raise ValueError(f"entity '{relationship[field]}' not found")

    def _validate_event(
        self, event: object, path: str, available_ids: set[str]
    ) -> None:
        if not isinstance(event, dict):
            raise ValueError(f"{path} must be a dict")
        entities = event.get("entities")
        if entities is None:
            return
        if not isinstance(entities, list):
            raise ValueError(f"{path}.entities must be a list")
        for entity_id in entities:
            if not isinstance(entity_id, str):
                raise ValueError(f"{path}.entities entries must be strings")
            if entity_id not in available_ids:
                raise ValueError(f"entity '{entity_id}' not found")

    def _apply_settlement_data(
        self, state: CanonicalState, chapter: dict, settlement_data: dict
    ) -> None:
        world = WorldModel(state)
        state.data["world"]["entities"].extend(
            deepcopy(settlement_data["new_entities"])
        )
        for entity_update in settlement_data["updated_entities"]:
            world.update_entity(
                entity_update["id"], **self._update_fields(entity_update)
            )
        for relationship in settlement_data["new_relationships"]:
            state.data["world"]["relationships"].append(deepcopy(relationship))
        state.data["timeline"]["events"].extend(deepcopy(settlement_data["events"]))
        state.data["foreshadows"].extend(
            deepcopy(settlement_data["foreshadow_updates"])
        )
        chapter["status"] = "settled"
        chapter["settled_at"] = _utcnow()

    def _update_fields(self, entity_update: dict) -> dict:
        return {
            key: deepcopy(value)
            for key, value in entity_update.items()
            if key in {"name", "type", "attributes", "visibility"}
        }


def _utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


__all__ = ["AlreadySettledError", "ChapterSettler"]
