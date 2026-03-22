from __future__ import annotations

import importlib

import pytest

from novel_runtime.state.canonical import CanonicalState


def test_draft_returns_structured_chapter_result() -> None:
    drafter_module = _load_drafter_module()

    result = drafter_module.ChapterDrafter().draft(_build_state(), 1)

    assert result.chapter == 1
    assert result.title == "Chapter 1"
    assert result.status == "draft"
    assert result.summary == "Mira takes the next step."
    assert result.content == "# Chapter 1\n\nMira takes the next step.\n"


def test_draft_requires_active_world_entity() -> None:
    drafter_module = _load_drafter_module()

    with pytest.raises(
        ValueError, match="chapter 1 draft requires at least one active world entity"
    ):
        drafter_module.ChapterDrafter().draft(
            CanonicalState.create_empty("Example Novel", "fantasy"),
            1,
        )


def test_draft_failure_requires_integer_chapter_number() -> None:
    drafter_module = _load_drafter_module()

    with pytest.raises(ValueError, match="chapter_number must be an integer"):
        drafter_module.ChapterDrafter().draft(_build_state(), "1")


def test_draft_failure_ignores_active_entities_with_blank_names() -> None:
    drafter_module = _load_drafter_module()
    state = CanonicalState.create_empty("Example Novel", "fantasy")
    state.data["world"]["entities"].extend(
        [
            {
                "id": "entity-1",
                "name": "   ",
                "type": "character",
                "attributes": {"role": "lead"},
                "visibility": "active",
            },
            {
                "id": "entity-2",
                "name": "Mira",
                "type": "character",
                "attributes": {"role": "lead"},
                "visibility": "hidden",
            },
        ]
    )

    with pytest.raises(
        ValueError, match="chapter 2 draft requires at least one active world entity"
    ):
        drafter_module.ChapterDrafter().draft(state, 2)


def _load_drafter_module():
    try:
        return importlib.import_module("novel_runtime.pipeline.drafter")
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.pipeline.drafter module is required for the chapter draft MVP contract"
        )


def _build_state() -> CanonicalState:
    state = CanonicalState.create_empty("Example Novel", "fantasy")
    state.data["world"]["entities"].append(
        {
            "id": "entity-1",
            "name": "Mira",
            "type": "character",
            "attributes": {"role": "lead"},
            "visibility": "active",
        }
    )
    return state
