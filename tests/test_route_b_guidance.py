import json
from pathlib import Path

from novel_runtime.pipeline.guider import ChapterGuider
from novel_runtime.state.canonical import CanonicalState

ROOT = Path(__file__).resolve().parents[1]


FIXTURE_PATH = (
    ROOT
    / "changes"
    / "make-chapter-guide-assisted-executable"
    / "fixtures"
    / "chapter-guide-v1.json"
)


def test_chapter_guider_emits_frozen_route_b_guidance_contract() -> None:
    state = CanonicalState.create_empty("mybook", "fantasy")
    state.data["world"]["entities"].append(
        {
            "id": "entity-1",
            "name": "Mira",
            "type": "character",
            "attributes": {"role": "lead"},
            "visibility": "active",
        }
    )

    guidance = ChapterGuider().guide(state, 1)

    expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["data"]
    assert guidance == expected


def test_chapter_guider_selects_first_valid_active_entity_deterministically() -> None:
    state = CanonicalState.create_empty("mybook", "fantasy")
    state.data["world"]["entities"].extend(
        [
            "not-a-dict",
            {
                "id": "entity-0",
                "name": "",
                "type": "character",
                "attributes": {},
                "visibility": "active",
            },
            {
                "id": "entity-hidden",
                "name": "Shade",
                "type": "character",
                "attributes": {},
                "visibility": "hidden",
            },
            {
                "id": "entity-1",
                "name": "Mira",
                "type": "character",
                "attributes": {},
                "visibility": "active",
            },
            {
                "id": "entity-2",
                "name": "Tarin",
                "type": "character",
                "attributes": {},
                "visibility": "active",
            },
        ]
    )

    guidance = ChapterGuider().guide(state, 4)

    assert guidance["guidance_id"] == "guide-chapter-4-route-b-v1"
    assert guidance["chapter"] == 4
    assert guidance["settlement_template"] == {
        "chapter": 4,
        "prose_path": "artifacts/chapter-4/chapter-4.md",
        "summary": "",
        "continuity_notes": [],
        "open_questions": [],
    }


def test_chapter_guider_is_non_mutating() -> None:
    state = CanonicalState.create_empty("mybook", "fantasy")
    state.data["world"]["entities"].append(
        {
            "id": "entity-1",
            "name": "Mira",
            "type": "character",
            "attributes": {"role": "lead"},
            "visibility": "active",
        }
    )
    before = json.loads(json.dumps(state.data, sort_keys=True))

    guidance = ChapterGuider().guide(state, 2)

    after = json.loads(json.dumps(state.data, sort_keys=True))
    assert guidance["chapter"] == 2
    assert after == before
