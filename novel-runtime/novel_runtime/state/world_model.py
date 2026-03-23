from __future__ import annotations

from copy import deepcopy

from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.schema import ALLOWED_ENTITY_TYPES, ALLOWED_VISIBILITIES


class WorldModelError(ValueError):
    pass


class DuplicateEntityError(WorldModelError):
    pass


class EntityNotFoundError(WorldModelError):
    pass


class WorldModel:
    def __init__(self, state: CanonicalState) -> None:
        self._state = state
        self._world = state.data["world"]

    def add_entity(
        self,
        name: str,
        entity_type: str,
        attributes: dict,
        visibility: str = "active",
    ) -> dict:
        self._ensure_unique_name(name)
        self._validate_entity_type(entity_type)
        self._validate_attributes(attributes)
        self._validate_visibility(visibility)

        entity = {
            "id": self._next_entity_id(),
            "name": name,
            "type": entity_type,
            "attributes": deepcopy(attributes),
            "visibility": visibility,
        }
        self._entities.append(entity)
        return deepcopy(entity)

    def update_entity(self, entity_id: str, **kwargs) -> dict:
        entity = self._find_entity(entity_id)
        if entity is None:
            raise EntityNotFoundError(f"entity '{entity_id}' not found")

        allowed_fields = {"name", "type", "attributes", "visibility"}
        unknown_fields = set(kwargs) - allowed_fields
        if unknown_fields:
            unknown_list = ", ".join(sorted(unknown_fields))
            raise ValueError(f"unknown entity fields: {unknown_list}")

        if "name" in kwargs and kwargs["name"] != entity["name"]:
            self._ensure_unique_name(kwargs["name"], exclude_id=entity_id)
            entity["name"] = kwargs["name"]
        if "type" in kwargs:
            self._validate_entity_type(kwargs["type"])
            entity["type"] = kwargs["type"]
        if "attributes" in kwargs:
            self._validate_attributes(kwargs["attributes"])
            entity["attributes"] = deepcopy(kwargs["attributes"])
        if "visibility" in kwargs:
            self._validate_visibility(kwargs["visibility"])
            entity["visibility"] = kwargs["visibility"]

        return deepcopy(entity)

    def get_entity(self, entity_id: str) -> dict | None:
        entity = self._find_entity(entity_id)
        return deepcopy(entity) if entity is not None else None

    def get_entity_by_name(self, name: str) -> dict | None:
        entity = next((item for item in self._entities if item["name"] == name), None)
        return deepcopy(entity) if entity is not None else None

    def list_entities(
        self,
        type_filter: str | None = None,
        visibility_filter: str | None = None,
    ) -> list[dict]:
        entities = self._entities
        if type_filter is not None:
            entities = [entity for entity in entities if entity["type"] == type_filter]
        if visibility_filter is not None:
            entities = [
                entity
                for entity in entities
                if entity["visibility"] == visibility_filter
            ]
        return deepcopy(entities)

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        since_chapter: int,
    ) -> dict:
        self._require_entity(source_id)
        self._require_entity(target_id)
        if not isinstance(rel_type, str):
            raise ValueError("relationship type must be a string")
        if type(since_chapter) is not int:
            raise ValueError("since_chapter must be an integer")

        relationship = {
            "source": source_id,
            "target": target_id,
            "type": rel_type,
            "since_chapter": since_chapter,
        }
        self._relationships.append(relationship)
        return deepcopy(relationship)

    def list_relationships(self, entity_id: str | None = None) -> list[dict]:
        relationships = self._relationships
        if entity_id is not None:
            relationships = [
                relationship
                for relationship in relationships
                if relationship["source"] == entity_id
                or relationship["target"] == entity_id
            ]
        return deepcopy(relationships)

    def delete_entity(self, entity_id: str) -> dict:
        entity = self._find_entity(entity_id)
        if entity is None:
            raise EntityNotFoundError(f"entity '{entity_id}' not found")

        self._world["entities"] = [
            existing for existing in self._entities if existing["id"] != entity_id
        ]
        self._world["relationships"] = [
            relationship
            for relationship in self._relationships
            if relationship["source"] != entity_id
            and relationship["target"] != entity_id
        ]
        return deepcopy(entity)

    @property
    def _entities(self) -> list[dict]:
        return self._world["entities"]

    @property
    def _relationships(self) -> list[dict]:
        return self._world["relationships"]

    def _find_entity(self, entity_id: str) -> dict | None:
        return next(
            (entity for entity in self._entities if entity["id"] == entity_id), None
        )

    def _require_entity(self, entity_id: str) -> dict:
        entity = self._find_entity(entity_id)
        if entity is None:
            raise EntityNotFoundError(f"entity '{entity_id}' not found")
        return entity

    def _ensure_unique_name(self, name: str, exclude_id: str | None = None) -> None:
        duplicate = next(
            (
                entity
                for entity in self._entities
                if entity["name"] == name and entity["id"] != exclude_id
            ),
            None,
        )
        if duplicate is not None:
            raise DuplicateEntityError(f"entity name '{name}' already exists")

    def _next_entity_id(self) -> str:
        used_ids = {entity["id"] for entity in self._entities}
        next_index = 1
        for entity_id in used_ids:
            prefix, sep, suffix = entity_id.rpartition("-")
            if prefix == "entity" and sep and suffix.isdigit():
                next_index = max(next_index, int(suffix) + 1)

        candidate = f"entity-{next_index}"
        while candidate in used_ids:
            next_index += 1
            candidate = f"entity-{next_index}"
        return candidate

    def _validate_entity_type(self, entity_type: str) -> None:
        if entity_type not in ALLOWED_ENTITY_TYPES:
            allowed = ", ".join(sorted(ALLOWED_ENTITY_TYPES))
            raise ValueError(f"entity type must be one of: {allowed}")

    def _validate_attributes(self, attributes: dict) -> None:
        if not isinstance(attributes, dict):
            raise ValueError("attributes must be a dict")

    def _validate_visibility(self, visibility: str) -> None:
        if visibility not in ALLOWED_VISIBILITIES:
            allowed = ", ".join(sorted(ALLOWED_VISIBILITIES))
            raise ValueError(f"visibility must be one of: {allowed}")


__all__ = [
    "DuplicateEntityError",
    "EntityNotFoundError",
    "WorldModel",
    "WorldModelError",
]
