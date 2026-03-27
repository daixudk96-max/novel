from __future__ import annotations

from copy import deepcopy

import pytest

from novel_runtime.pipeline.settler import AlreadySettledError, ChapterSettler
from novel_runtime.state.canonical import CanonicalState


def test_settle_updates_chapter_status() -> None:
    state = _build_state()

    updated_state = ChapterSettler().settle(
        state,
        1,
        "Mira reached the vault.",
        _settlement_data(),
    )

    chapter = updated_state.data["chapters"][0]
    assert chapter["status"] == "settled"
    assert chapter["settled_at"].endswith("Z")


def test_settle_adds_new_entities() -> None:
    state = _build_state()

    updated_state = ChapterSettler().settle(
        state,
        1,
        "Mira reached the vault.",
        _settlement_data(),
    )

    assert updated_state.data["world"]["entities"][-1] == {
        "id": "entity-2",
        "name": "Sunspire Vault",
        "type": "location",
        "attributes": {"security": "sealed"},
        "visibility": "reference",
    }


def test_settle_updates_existing_entities() -> None:
    state = _build_state()

    updated_state = ChapterSettler().settle(
        state,
        1,
        "Mira reached the vault.",
        _settlement_data(),
    )

    assert updated_state.data["world"]["entities"][0] == {
        "id": "entity-1",
        "name": "Mira",
        "type": "character",
        "attributes": {"role": "lead", "location": "Sunspire Vault"},
        "visibility": "active",
    }


def test_settle_adds_events() -> None:
    state = _build_state()

    updated_state = ChapterSettler().settle(
        state,
        1,
        "Mira reached the vault.",
        _settlement_data(),
    )

    assert updated_state.data["timeline"]["events"] == [
        {
            "chapter": 1,
            "type": "discovery",
            "summary": "Mira discovers the sealed Sunspire Vault.",
            "entities": ["entity-1", "entity-2"],
        }
    ]


def test_settle_invalid_entity_reference_fails_without_partial_mutation() -> None:
    state = _build_state()

    with pytest.raises(ValueError, match="missing-entity"):
        ChapterSettler().settle(
            state,
            1,
            "Mira reached the vault.",
            {
                **_settlement_data(),
                "updated_entities": [
                    {"id": "missing-entity", "attributes": {"location": "Nowhere"}}
                ],
            },
        )

    assert state.data == _build_state().data


def test_settle_already_settled_raises() -> None:
    state = _build_state()
    state.data["chapters"][0]["status"] = "settled"
    state.data["chapters"][0]["settled_at"] = "2026-03-20T00:00:00Z"

    with pytest.raises(AlreadySettledError, match="1"):
        ChapterSettler().settle(state, 1, "Mira reached the vault.", _settlement_data())


def test_settle_bootstraps_missing_row_atomically() -> None:
    state = _build_state(include_chapter=False)

    updated_state = ChapterSettler().settle(
        state,
        1,
        "Mira reached the vault.",
        _settlement_data(),
    )

    assert updated_state.data["chapters"] == [
        {
            "number": 1,
            "title": "Chapter 1",
            "status": "settled",
            "summary": "",
            "settled_at": updated_state.data["chapters"][0]["settled_at"],
        }
    ]
    assert updated_state.data["chapters"][0]["settled_at"].endswith("Z")


def test_settle_failure_leaves_state_unchanged_for_guided_ingress() -> None:
    state = _build_state(include_chapter=False)
    before = deepcopy(state.data)

    with pytest.raises(ValueError, match="missing-entity"):
        ChapterSettler().settle(
            state,
            1,
            "Mira reached the vault.",
            {
                **_settlement_data(),
                "updated_entities": [
                    {"id": "missing-entity", "attributes": {"location": "Nowhere"}}
                ],
            },
        )

    assert state.data == before


def _build_state(*, include_chapter: bool = True) -> CanonicalState:
    state = CanonicalState.create_empty("Settler Novel", "fantasy")
    state.data["world"]["entities"].append(
        {
            "id": "entity-1",
            "name": "Mira",
            "type": "character",
            "attributes": {"role": "lead"},
            "visibility": "active",
        }
    )
    if include_chapter:
        state.data["chapters"].append(
            {
                "number": 1,
                "title": "Arrival",
                "status": "draft",
                "summary": "Mira searches the ridge for the hidden vault.",
                "settled_at": "",
            }
        )
    return state


def _settlement_data() -> dict:
    return {
        "new_entities": [
            {
                "id": "entity-2",
                "name": "Sunspire Vault",
                "type": "location",
                "attributes": {"security": "sealed"},
                "visibility": "reference",
            }
        ],
        "updated_entities": [
            {
                "id": "entity-1",
                "attributes": {"role": "lead", "location": "Sunspire Vault"},
            }
        ],
        "new_relationships": [
            {
                "source": "entity-1",
                "target": "entity-2",
                "type": "discovers",
                "since_chapter": 1,
            }
        ],
        "events": [
            {
                "chapter": 1,
                "type": "discovery",
                "summary": "Mira discovers the sealed Sunspire Vault.",
                "entities": ["entity-1", "entity-2"],
            }
        ],
        "foreshadow_updates": [
            {
                "id": "foreshadow-1",
                "status": "seeded",
                "chapter": 1,
            }
        ],
    }
