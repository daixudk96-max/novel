from __future__ import annotations

from novel_runtime.pipeline.postcheck import PostcheckRunner
from novel_runtime.state.canonical import CanonicalState


def test_unregistered_name_detected() -> None:
    state = _build_state()

    result = PostcheckRunner().run(
        state,
        1,
        "Mira crossed the ridge and met Taryn at the gate.",
    )

    assert result.passed is False
    assert result.issues[0].rule == "unregistered-name"
    assert result.issues[0].severity == "blocker"
    assert result.issues[0].location["excerpt"] == "Taryn"


def test_hidden_entity_appearance_detected() -> None:
    state = _build_state()

    result = PostcheckRunner().run(
        state,
        1,
        "Mira spotted Shade in the tower window.",
    )

    assert result.passed is False
    assert [issue.rule for issue in result.issues] == ["hidden-entity-appearance"]
    assert result.issues[0].severity == "blocker"


def test_ai_cliche_detected() -> None:
    state = _build_state()

    result = PostcheckRunner().run(
        state,
        1,
        "Mira paused. It is important to note that the ridge was silent.",
    )

    assert result.passed is True
    assert [issue.rule for issue in result.issues] == ["ai-cliche"]
    assert result.issues[0].severity == "minor"


def test_clean_text_passes() -> None:
    state = _build_state()

    result = PostcheckRunner().run(
        state,
        1,
        "Mira crossed the ridge before dawn and reached Emberfall.",
    )

    assert result.passed is True
    assert result.issues == []


def test_sentence_initial_prose_word_is_not_flagged_as_unregistered_name() -> None:
    state = _build_state()

    result = PostcheckRunner().run(
        state,
        1,
        "Silent rain fell over Emberfall.",
    )

    assert result.passed is True
    assert [issue.rule for issue in result.issues] == []


def test_no_world_model_warns_without_crashing() -> None:
    state = CanonicalState.create_empty("Example Novel", "fantasy")
    _add_chapter(state, number=1, title="Blank", summary="Quiet road.")

    result = PostcheckRunner().run(state, 1, "A quiet road stretched toward the hills.")

    assert result.passed is True
    assert [issue.rule for issue in result.issues] == ["world-model-missing"]
    assert result.issues[0].severity == "minor"


def test_severity_levels_include_blocker_major_and_minor() -> None:
    state = _build_state()
    state.data["timeline"]["events"].append(
        {
            "chapter": 1,
            "time_marker": "Day 1",
            "summary": "Mira reached Emberfall on Day 1.",
        }
    )

    result = PostcheckRunner().run(
        state,
        1,
        "Day 2 began as Mira met Taryn while Shade watched from Emberfall. It is important to note that the bells were still.",
    )

    severities = {issue.rule: issue.severity for issue in result.issues}

    assert severities == {
        "unregistered-name": "blocker",
        "timeline-jump": "major",
        "hidden-entity-appearance": "blocker",
        "ai-cliche": "minor",
    }


def _build_state() -> CanonicalState:
    state = CanonicalState.create_empty("Example Novel", "fantasy")
    state.data["world"]["entities"].extend(
        [
            {
                "id": "entity-1",
                "name": "Mira",
                "type": "character",
                "attributes": {"role": "lead"},
                "visibility": "active",
            },
            {
                "id": "entity-2",
                "name": "Emberfall",
                "type": "location",
                "attributes": {"kind": "city"},
                "visibility": "active",
            },
            {
                "id": "entity-3",
                "name": "Shade",
                "type": "character",
                "attributes": {"role": "spy"},
                "visibility": "hidden",
            },
        ]
    )
    _add_chapter(state, number=1, title="Arrival", summary="Mira approaches Emberfall.")
    return state


def _add_chapter(state: CanonicalState, number: int, title: str, summary: str) -> None:
    state.data["chapters"].append(
        {
            "number": number,
            "title": title,
            "status": "draft",
            "summary": summary,
            "settled_at": "",
        }
    )
