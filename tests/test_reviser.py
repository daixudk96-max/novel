from __future__ import annotations

import inspect
import importlib

import pytest


def test_revise_returns_structured_revision_result_for_audit_issues() -> None:
    reviser_module = _load_reviser_module()
    auditor_module = importlib.import_module("novel_runtime.pipeline.auditor")
    chapter_text = "Mira crossed the ridge and met Taryn at Emberfall."
    issues = [
        auditor_module.AuditIssue(
            rule="unregistered-name",
            severity="blocker",
            message="unregistered character or location 'Taryn' found in chapter text",
            location={"line": 1, "start": 31, "end": 36, "excerpt": "Taryn"},
        )
    ]

    result = reviser_module.ChapterReviser().revise(1, chapter_text, issues)

    assert result.chapter == 1
    assert result.revised_text == (
        "Mira crossed the ridge and met Taryn at Emberfall.\n"
        "<!-- REVISION NOTE: unregistered-name - "
        "unregistered character or location 'Taryn' found in chapter text -->"
    )
    assert result.revision_log == [
        "<!-- REVISION NOTE: unregistered-name - "
        "unregistered character or location 'Taryn' found in chapter text -->"
    ]
    assert result.issues_addressed == [
        {
            "rule": "unregistered-name",
            "severity": "blocker",
            "message": "unregistered character or location 'Taryn' found in chapter text",
            "location": {"line": 1, "start": 31, "end": 36, "excerpt": "Taryn"},
        }
    ]


def test_revise_returns_original_text_when_no_revision_is_needed() -> None:
    reviser_module = _load_reviser_module()
    chapter_text = "Mira crossed the ridge before dawn and reached Emberfall."

    result = reviser_module.ChapterReviser().revise(1, chapter_text, [])

    assert result.chapter == 1
    assert result.revised_text == chapter_text
    assert result.revision_log == []
    assert result.issues_addressed == []


def test_revise_locks_output_only_signature_and_defers_downstream_steps() -> None:
    reviser_module = _load_reviser_module()

    assert list(inspect.signature(reviser_module.ChapterReviser.revise).parameters) == [
        "self",
        "chapter_number",
        "chapter_text",
        "issues",
    ], (
        "revise must stay output-only; settle/postcheck/approve/LLM remain deferred downstream steps"
    )


def test_revise_copies_issue_payloads_without_mutating_input_issue_state() -> None:
    reviser_module = _load_reviser_module()
    auditor_module = importlib.import_module("novel_runtime.pipeline.auditor")
    issue = auditor_module.AuditIssue(
        rule="continuity-gap",
        severity="major",
        message="chapter contradicts prior event",
        location={"line": 4, "start": 0, "end": 12, "excerpt": ""},
    )

    result = reviser_module.ChapterReviser().revise(2, "Scene text.", [issue])
    issue.location["line"] = 99

    assert result.issues_addressed == [
        {
            "rule": "continuity-gap",
            "severity": "major",
            "message": "chapter contradicts prior event",
            "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
        }
    ]


def _load_reviser_module():
    try:
        return importlib.import_module("novel_runtime.pipeline.reviser")
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.pipeline.reviser module is required for the chapter revise MVP contract"
        )
