from __future__ import annotations

ALLOWED_ENTITY_TYPES = frozenset(
    {"character", "location", "item", "faction", "concept"}
)
ALLOWED_VISIBILITIES = frozenset({"active", "reference", "hidden"})
ALLOWED_CHAPTER_STATUSES = frozenset({"draft", "settled", "checked", "approved"})

CANONICAL_STATE_SCHEMA = {
    "type": "object",
    "required": ["version", "project", "world", "timeline", "foreshadows", "chapters"],
    "properties": {
        "version": {"type": "integer", "const": 1},
        "project": {
            "type": "object",
            "required": ["name", "genre", "created_at"],
            "properties": {
                "name": {"type": "string"},
                "genre": {"type": "string"},
                "created_at": {"type": "string"},
            },
        },
        "world": {
            "type": "object",
            "required": ["entities", "relationships"],
            "properties": {
                "entities": {
                    "type": "array",
                    "item": {
                        "type": "object",
                        "required": ["id", "name", "type", "attributes", "visibility"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": sorted(ALLOWED_ENTITY_TYPES),
                            },
                            "attributes": {"type": "object"},
                            "visibility": {
                                "type": "string",
                                "enum": sorted(ALLOWED_VISIBILITIES),
                            },
                        },
                    },
                },
                "relationships": {
                    "type": "array",
                    "item": {
                        "type": "object",
                        "required": ["source", "target", "type", "since_chapter"],
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "type": {"type": "string"},
                            "since_chapter": {"type": "integer"},
                        },
                    },
                },
            },
        },
        "timeline": {
            "type": "object",
            "required": ["current_chapter", "events"],
            "properties": {
                "current_chapter": {"type": "integer"},
                "events": {"type": "array"},
            },
        },
        "foreshadows": {"type": "array"},
        "chapters": {
            "type": "array",
            "item": {
                "type": "object",
                "required": ["number", "title", "status", "summary", "settled_at"],
                "properties": {
                    "number": {"type": "integer"},
                    "title": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": sorted(ALLOWED_CHAPTER_STATUSES),
                    },
                    "summary": {"type": "string"},
                    "settled_at": {"type": "string"},
                },
            },
        },
    },
}


class SchemaValidationError(ValueError):
    pass


def validate_state(data: object) -> dict:
    if not isinstance(data, dict):
        raise SchemaValidationError("state must be a dict")

    _require_keys(data, CANONICAL_STATE_SCHEMA["required"], "state")
    _validate_version(data["version"])
    _validate_project(data["project"])
    _validate_world(data["world"])
    _validate_timeline(data["timeline"])
    _validate_list(data["foreshadows"], "foreshadows")
    _validate_chapters(data["chapters"])
    return data


def _require_keys(data: dict, required: list[str], path: str) -> None:
    for key in required:
        if key not in data:
            raise SchemaValidationError(f"{path} missing required field '{key}'")


def _validate_version(value: object) -> None:
    if type(value) is not int:
        raise SchemaValidationError("version must be an integer")
    if value != 1:
        raise SchemaValidationError("version must be 1")


def _validate_project(project: object) -> None:
    if not isinstance(project, dict):
        raise SchemaValidationError("project must be a dict")
    _require_keys(project, ["name", "genre", "created_at"], "project")

    for field in ("name", "genre", "created_at"):
        if not isinstance(project[field], str):
            raise SchemaValidationError(f"project.{field} must be a string")


def _validate_world(world: object) -> None:
    if not isinstance(world, dict):
        raise SchemaValidationError("world must be a dict")
    _require_keys(world, ["entities", "relationships"], "world")
    _validate_entities(world["entities"])
    _validate_relationships(world["relationships"])


def _validate_entities(entities: object) -> None:
    _validate_list(entities, "world.entities")

    for index, entity in enumerate(entities):
        path = f"world.entities[{index}]"
        if not isinstance(entity, dict):
            raise SchemaValidationError(f"{path} must be a dict")

        _require_keys(entity, ["id", "name", "type", "attributes", "visibility"], path)

        for field in ("id", "name"):
            if not isinstance(entity[field], str):
                raise SchemaValidationError(f"{path}.{field} must be a string")

        if entity["type"] not in ALLOWED_ENTITY_TYPES:
            allowed = ", ".join(sorted(ALLOWED_ENTITY_TYPES))
            raise SchemaValidationError(
                f"{path} has invalid entity type '{entity['type']}'. Allowed: {allowed}"
            )

        if not isinstance(entity["attributes"], dict):
            raise SchemaValidationError(f"{path}.attributes must be a dict")

        if entity["visibility"] not in ALLOWED_VISIBILITIES:
            allowed = ", ".join(sorted(ALLOWED_VISIBILITIES))
            raise SchemaValidationError(f"{path}.visibility must be one of: {allowed}")


def _validate_relationships(relationships: object) -> None:
    _validate_list(relationships, "world.relationships")

    for index, relationship in enumerate(relationships):
        path = f"world.relationships[{index}]"
        if not isinstance(relationship, dict):
            raise SchemaValidationError(f"{path} must be a dict")

        _require_keys(relationship, ["source", "target", "type", "since_chapter"], path)

        for field in ("source", "target", "type"):
            if not isinstance(relationship[field], str):
                raise SchemaValidationError(f"{path}.{field} must be a string")

        if type(relationship["since_chapter"]) is not int:
            raise SchemaValidationError(f"{path}.since_chapter must be an integer")


def _validate_timeline(timeline: object) -> None:
    if not isinstance(timeline, dict):
        raise SchemaValidationError("timeline must be a dict")
    _require_keys(timeline, ["current_chapter", "events"], "timeline")

    if type(timeline["current_chapter"]) is not int:
        raise SchemaValidationError("timeline.current_chapter must be an integer")

    _validate_list(timeline["events"], "timeline.events")


def _validate_chapters(chapters: object) -> None:
    _validate_list(chapters, "chapters")

    for index, chapter in enumerate(chapters):
        path = f"chapters[{index}]"
        if not isinstance(chapter, dict):
            raise SchemaValidationError(f"{path} must be a dict")

        _require_keys(
            chapter, ["number", "title", "status", "summary", "settled_at"], path
        )

        if type(chapter["number"]) is not int:
            raise SchemaValidationError(f"{path}.number must be an integer")

        for field in ("title", "summary", "settled_at"):
            if not isinstance(chapter[field], str):
                raise SchemaValidationError(f"{path}.{field} must be a string")

        if chapter["status"] not in ALLOWED_CHAPTER_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_CHAPTER_STATUSES))
            raise SchemaValidationError(
                f"{path} has invalid chapter status '{chapter['status']}'. Allowed: {allowed}"
            )


def _validate_list(value: object, path: str) -> None:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{path} must be a list")
