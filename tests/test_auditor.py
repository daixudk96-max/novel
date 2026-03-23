from __future__ import annotations

import importlib
from copy import deepcopy

from novel_runtime.state.canonical import CanonicalState


def test_audit_runner_returns_pass_contract() -> None:
    state = _build_state()

    payload = _run_audit(
        state,
        1,
        "Mira crossed the ridge before dawn and reached Emberfall.",
    )

    assert payload == {
        "chapter": 1,
        "status": "pass",
        "severity": "none",
        "recommended_action": "proceed_to_snapshot",
        "issues": [],
    }


def test_audit_runner_returns_failure_contract() -> None:
    state = _build_state()

    payload = _run_audit(
        state,
        1,
        "Mira crossed the ridge and met Taryn at Emberfall.",
    )

    assert payload == {
        "chapter": 1,
        "status": "fail",
        "severity": "blocker",
        "recommended_action": "revise_chapter",
        "issues": [
            {
                "rule": "unregistered-name",
                "severity": "blocker",
                "message": "unregistered character or location 'Taryn' found in chapter text",
                "location": {
                    "line": 1,
                    "start": 31,
                    "end": 36,
                    "excerpt": "Taryn",
                },
            }
        ],
    }


def test_audit_runner_returns_pass_contract_with_minor_only_findings() -> None:
    module = importlib.import_module("novel_runtime.pipeline.auditor")
    postcheck_module = importlib.import_module("novel_runtime.pipeline.postcheck")
    state = _build_state()
    runner = _StubPostcheckRunner(
        postcheck_module.PostcheckResult(
            passed=True,
            issues=[
                postcheck_module.PostcheckIssue(
                    rule="world-model-missing",
                    severity="minor",
                    message="world model is empty; entity-based checks were skipped",
                    location={"line": 1, "start": 0, "end": 0, "excerpt": ""},
                )
            ],
        )
    )

    result = module.ChapterAuditor(postcheck_runner=runner).run(
        state,
        1,
        "Mira crossed the ridge before dawn and reached Emberfall.",
    )

    assert result.to_dict() == {
        "chapter": 1,
        "status": "pass",
        "severity": "minor",
        "recommended_action": "proceed_to_snapshot",
        "issues": [
            {
                "rule": "world-model-missing",
                "severity": "minor",
                "message": "world model is empty; entity-based checks were skipped",
                "location": {"line": 1, "start": 0, "end": 0, "excerpt": ""},
            }
        ],
    }


def test_audit_runner_reuses_postcheck_runner_findings() -> None:
    module = importlib.import_module("novel_runtime.pipeline.auditor")
    postcheck_module = importlib.import_module("novel_runtime.pipeline.postcheck")
    state = _build_state()
    runner = _StubPostcheckRunner(
        postcheck_module.PostcheckResult(
            passed=False,
            issues=[
                postcheck_module.PostcheckIssue(
                    rule="from-postcheck",
                    severity="major",
                    message="reused postcheck finding",
                    location={"line": 4, "start": 12, "end": 19, "excerpt": "signal"},
                )
            ],
        )
    )

    result = module.ChapterAuditor(postcheck_runner=runner).run(
        state,
        2,
        "Chapter text that would not naturally trigger that exact rule.",
    )
    payload = result.to_dict()

    assert runner.calls == [
        (state, 2, "Chapter text that would not naturally trigger that exact rule.")
    ]
    assert payload == {
        "chapter": 2,
        "status": "fail",
        "severity": "major",
        "recommended_action": "revise_chapter",
        "issues": [
            {
                "rule": "from-postcheck",
                "severity": "major",
                "message": "reused postcheck finding",
                "location": {
                    "line": 4,
                    "start": 12,
                    "end": 19,
                    "excerpt": "signal",
                },
            }
        ],
    }


def test_audit_runner_wraps_postcheck_issue_without_aliasing_location() -> None:
    module = importlib.import_module("novel_runtime.pipeline.auditor")
    postcheck_module = importlib.import_module("novel_runtime.pipeline.postcheck")
    state = _build_state()
    shared_location = {"line": 7, "start": 3, "end": 8, "excerpt": "Beacon"}
    runner = _StubPostcheckRunner(
        postcheck_module.PostcheckResult(
            passed=True,
            issues=[
                postcheck_module.PostcheckIssue(
                    rule="shared-location",
                    severity="minor",
                    message="location should be copied",
                    location=shared_location,
                )
            ],
        )
    )

    result = module.ChapterAuditor(postcheck_runner=runner).run(state, 1, "Beacon")
    shared_location["excerpt"] = "mutated after audit"

    assert result.to_dict()["status"] == "pass"
    assert result.to_dict()["recommended_action"] == "proceed_to_snapshot"
    assert result.to_dict()["issues"] == [
        {
            "rule": "shared-location",
            "severity": "minor",
            "message": "location should be copied",
            "location": {"line": 7, "start": 3, "end": 8, "excerpt": "Beacon"},
        }
    ]


def test_audit_runner_keeps_canonical_state_report_only() -> None:
    state = _build_state()
    before = deepcopy(state.data)

    payload = _run_audit(
        state,
        1,
        "Mira crossed the ridge and met Taryn at Emberfall.",
    )

    assert payload["recommended_action"] == "revise_chapter"
    assert state.data == before


def _run_audit(state: CanonicalState, chapter_number: int, chapter_text: str) -> dict:
    module = importlib.import_module("novel_runtime.pipeline.auditor")
    auditor = module.ChapterAuditor()
    result = auditor.run(state, chapter_number, chapter_text)
    if hasattr(result, "to_dict"):
        return result.to_dict()
    assert isinstance(result, dict)
    return result


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
        ]
    )
    state.data["chapters"].append(
        {
            "number": 1,
            "title": "Arrival",
            "status": "settled",
            "summary": "Mira approaches Emberfall.",
            "settled_at": "2026-03-22T12:34:56Z",
        }
    )
    return state


class _StubPostcheckRunner:
    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[tuple[CanonicalState, int, str]] = []

    def run(self, state: CanonicalState, chapter_number: int, chapter_text: str):
        self.calls.append((state, chapter_number, chapter_text))
        return self._result
