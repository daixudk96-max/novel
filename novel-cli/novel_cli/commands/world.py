from __future__ import annotations

import json
from pathlib import Path
from typing import Never

import click
from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.schema import ALLOWED_ENTITY_TYPES, ALLOWED_VISIBILITIES
from novel_runtime.state.world_model import (
    DuplicateEntityError,
    EntityNotFoundError,
    WorldModel,
)

from novel_cli.commands.project import _emit, _fail, _resolve_project_dir


@click.group(name="world")
def world_group() -> None:
    pass


@world_group.group(name="entity")
def entity_group() -> None:
    pass


@entity_group.command("add")
@click.option("--name", required=True)
@click.option(
    "--type",
    "entity_type",
    required=True,
    type=click.Choice(sorted(ALLOWED_ENTITY_TYPES)),
)
@click.option("--attributes", default="{}")
@click.option(
    "--visibility",
    default="active",
    show_default=True,
    type=click.Choice(sorted(ALLOWED_VISIBILITIES)),
)
@click.option("--json", "json_output", is_flag=True)
def add_entity(
    name: str,
    entity_type: str,
    attributes: str,
    visibility: str,
    json_output: bool,
) -> None:
    state, project_dir, world = _load_world_model()
    try:
        entity = world.add_entity(
            name=name,
            entity_type=entity_type,
            attributes=_parse_attributes(attributes, json_output),
            visibility=visibility,
        )
    except (DuplicateEntityError, ValueError) as exc:
        _raise_fail(str(exc), json_output)
    else:
        state.save(project_dir)
        payload = {"entity": entity}
        _emit(payload, f"Added entity '{entity['name']}' ({entity['id']})", json_output)


@entity_group.command("update")
@click.option("--id", "entity_id", required=True)
@click.option("--name")
@click.option("--attributes")
@click.option("--json", "json_output", is_flag=True)
def update_entity(
    entity_id: str,
    name: str | None,
    attributes: str | None,
    json_output: bool,
) -> None:
    state, project_dir, world = _load_world_model()
    updates: dict[str, object] = {}
    if name is not None:
        updates["name"] = name
    if attributes is not None:
        updates["attributes"] = _parse_attributes(attributes, json_output)
    if not updates:
        _raise_fail("no updates provided", json_output)

    try:
        entity = world.update_entity(entity_id, **updates)
    except (DuplicateEntityError, EntityNotFoundError, ValueError) as exc:
        _raise_fail(str(exc), json_output)
    else:
        state.save(project_dir)
        payload = {"entity": entity}
        _emit(
            payload, f"Updated entity '{entity['name']}' ({entity['id']})", json_output
        )


@entity_group.command("show")
@click.option("--id", "entity_id")
@click.option("--name", "entity_name")
@click.option("--json", "json_output", is_flag=True)
def show_entity(
    entity_id: str | None, entity_name: str | None, json_output: bool
) -> None:
    state, _, world = _load_world_model()
    del state
    _require_exactly_one_lookup(entity_id, entity_name, json_output)
    entity = (
        world.get_entity(entity_id)
        if entity_id is not None
        else world.get_entity_by_name(entity_name or "")
    )
    if entity is None:
        lookup = entity_id if entity_id is not None else entity_name
        _raise_fail(f"entity '{lookup}' not found", json_output)

    payload = {"entity": entity}
    text = "\n".join(
        (
            f"ID: {entity['id']}",
            f"Name: {entity['name']}",
            f"Type: {entity['type']}",
            f"Visibility: {entity['visibility']}",
            f"Attributes: {json.dumps(entity['attributes'], ensure_ascii=False, sort_keys=True)}",
        )
    )
    _emit(payload, text, json_output)


@entity_group.command("list")
@click.option("--type", "entity_type", type=click.Choice(sorted(ALLOWED_ENTITY_TYPES)))
@click.option("--visibility", type=click.Choice(sorted(ALLOWED_VISIBILITIES)))
@click.option("--json", "json_output", is_flag=True)
def list_entities(
    entity_type: str | None, visibility: str | None, json_output: bool
) -> None:
    state, _, world = _load_world_model()
    del state
    entities = world.list_entities(
        type_filter=entity_type, visibility_filter=visibility
    )
    payload = {"count": len(entities), "entities": entities}
    if entities:
        text = "\n".join(
            f"{entity['id']} | {entity['name']} | {entity['type']} | {entity['visibility']}"
            for entity in entities
        )
    else:
        text = "No entities found"
    _emit(payload, text, json_output)


@world_group.group(name="relationship")
def relationship_group() -> None:
    pass


@relationship_group.command("add")
@click.option("--source", required=True)
@click.option("--target", required=True)
@click.option("--type", "relationship_type", required=True)
@click.option("--since-chapter", default=0, show_default=True, type=int)
@click.option("--json", "json_output", is_flag=True)
def add_relationship(
    source: str,
    target: str,
    relationship_type: str,
    since_chapter: int,
    json_output: bool,
) -> None:
    state, project_dir, world = _load_world_model()
    try:
        relationship = world.add_relationship(
            source_id=source,
            target_id=target,
            rel_type=relationship_type,
            since_chapter=since_chapter,
        )
    except (EntityNotFoundError, ValueError) as exc:
        _raise_fail(str(exc), json_output)
    else:
        state.save(project_dir)
        payload = {"relationship": relationship}
        _emit(
            payload,
            f"Added relationship {source} -> {target} ({relationship_type})",
            json_output,
        )


@relationship_group.command("list")
@click.option("--entity", "entity_id")
@click.option("--json", "json_output", is_flag=True)
def list_relationships(entity_id: str | None, json_output: bool) -> None:
    state, _, world = _load_world_model()
    del state
    relationships = world.list_relationships(entity_id=entity_id)
    payload = {"count": len(relationships), "relationships": relationships}
    if relationships:
        text = "\n".join(
            f"{relationship['source']} -> {relationship['target']} | {relationship['type']} | since chapter {relationship['since_chapter']}"
            for relationship in relationships
        )
    else:
        text = "No relationships found"
    _emit(payload, text, json_output)


def _load_world_model() -> tuple[CanonicalState, Path, WorldModel]:
    project_dir = _resolve_project_dir()
    state = CanonicalState.load(project_dir)
    return state, project_dir, WorldModel(state)


def _parse_attributes(value: str, json_output: bool) -> dict:
    payload: object | None = None
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        _raise_fail(f"invalid attributes JSON: {exc.msg}", json_output)

    if not isinstance(payload, dict):
        _raise_fail("attributes must decode to a JSON object", json_output)
    return payload


def _require_exactly_one_lookup(
    entity_id: str | None, entity_name: str | None, json_output: bool
) -> None:
    if (entity_id is None) == (entity_name is None):
        _raise_fail("provide exactly one of --id or --name", json_output)


def _raise_fail(message: str, json_output: bool) -> Never:
    _fail(message, json_output)
    raise AssertionError("unreachable")


__all__ = ["world_group"]
