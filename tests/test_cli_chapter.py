import json
from pathlib import Path

import click
from click.testing import CliRunner
from novel_runtime.state.canonical import CanonicalState

from novel_cli.main import cli


def test_chapter_help_locks_current_executable_surface() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["chapter", "--help"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "draft" in result.output
    assert "settle" in result.output
    assert "postcheck" in result.output
    assert "audit" in result.output
    assert "route" in result.output
    assert "revise" in result.output
    assert "approve" in result.output


def test_approve_returns_plain_text_for_passing_audit_without_revision() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(1)
        audit_path = _write_audit_file(
            {
                "chapter": 1,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issues": [],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "approve",
                "--chapter",
                "1",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert result.output == (
            "Chapter: 1\n"
            "Status: approved\n"
            "Reason: audit passed and chapter is ready for snapshot\n"
            "Conditions: none\n"
        )


def test_approve_returns_json_for_failed_audit_with_revision_file() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(2)
        audit_path = _write_audit_file(
            {
                "chapter": 2,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
            }
        )
        revision_path = _write_revision_file(
            {
                "chapter": 2,
                "path": str(
                    (Path.cwd() / "chapters" / "chapter_2_revised.md").resolve()
                ),
                "revised_text": "Scene text.\n<!-- REVISION NOTE: continuity-gap - chapter contradicts prior event -->",
                "revision_log": [
                    "<!-- REVISION NOTE: continuity-gap - chapter contradicts prior event -->"
                ],
                "issues_addressed": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
                "routing_action": "revise",
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "approve",
                "--chapter",
                "2",
                "--audit-file",
                str(audit_path),
                "--revision-file",
                str(revision_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "chapter": 2,
            "status": "conditionally_approved",
            "reason": "audit failed, but revision addressed 1 issues",
            "conditions": ["confirm continuity-gap remains resolved before snapshot"],
        }


def test_approve_returns_non_zero_for_failed_audit_without_revision_file() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(3)
        audit_path = _write_audit_file(
            {
                "chapter": 3,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "motivation-gap",
                        "severity": "major",
                        "message": "motivation is unclear",
                        "location": {"line": 7, "start": 0, "end": 15, "excerpt": ""},
                    }
                ],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "approve",
                "--chapter",
                "3",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert result.output == (
            "Chapter: 3\n"
            "Status: rejected\n"
            "Reason: audit failed and no revision was provided\n"
            "Conditions:\n"
            "- provide a revision that addresses the audit issues\n"
        )


def test_approve_rejects_invalid_audit_file_input() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(4)
        audit_path = Path("audit.json")
        audit_path.write_text("[]", encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "chapter",
                "approve",
                "--chapter",
                "4",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert result.output == "Error: audit file must decode to a JSON object\n"


def test_approve_rejects_audit_file_for_different_chapter() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(5)
        audit_path = _write_audit_file(
            {
                "chapter": 4,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issues": [],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "approve",
                "--chapter",
                "5",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert (
            result.output
            == "Error: audit file chapter '4' does not match --chapter '5'\n"
        )


def test_approve_rejects_malformed_revision_file_input() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(6)
        audit_path = _write_audit_file(
            {
                "chapter": 6,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
            }
        )
        revision_path = _write_revision_file(
            {
                "chapter": 6,
                "path": str(
                    (Path.cwd() / "chapters" / "chapter_6_revised.md").resolve()
                ),
                "revised_text": "Scene text.",
                "revision_log": [],
                "issues_addressed": [{"message": "missing rule", "location": {}}],
                "routing_action": "revise",
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "approve",
                "--chapter",
                "6",
                "--audit-file",
                str(audit_path),
                "--revision-file",
                str(revision_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert (
            result.output
            == "Error: invalid revision file JSON: expected revision result object\n"
        )


def test_approve_keeps_canonical_state_output_only_and_defers_downstream_steps(
    monkeypatch,
) -> None:
    from novel_cli.commands import chapter as chapter_commands

    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(6)
        audit_path = _write_audit_file(
            {
                "chapter": 6,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
            }
        )
        revision_path = _write_revision_file(
            {
                "chapter": 6,
                "path": str(
                    (Path.cwd() / "chapters" / "chapter_6_revised.md").resolve()
                ),
                "revised_text": "Guardrail scene.\n<!-- REVISION NOTE: continuity-gap - chapter contradicts prior event -->",
                "revision_log": [
                    "<!-- REVISION NOTE: continuity-gap - chapter contradicts prior event -->"
                ],
                "issues_addressed": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
                "routing_action": "revise",
            }
        )
        before_state = json.loads(
            json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
        )
        before_files = _project_files()

        class UnexpectedSettler:
            def __init__(self, *args, **kwargs) -> None:
                raise AssertionError(
                    "approve must not invoke settle; that remains deferred"
                )

        class UnexpectedPostcheckRunner:
            def __init__(self, *args, **kwargs) -> None:
                raise AssertionError(
                    "approve must not invoke postcheck; that remains deferred"
                )

        def unexpected_save(self, project_dir: Path) -> None:
            raise AssertionError("approve must not save canonical state")

        def unexpected_prompt(*args, **kwargs):
            raise AssertionError(
                "approve must not introduce interactive prompts; interactive/LLM approval remains deferred"
            )

        monkeypatch.setattr(chapter_commands, "ChapterSettler", UnexpectedSettler)
        monkeypatch.setattr(
            chapter_commands, "PostcheckRunner", UnexpectedPostcheckRunner
        )
        monkeypatch.setattr(CanonicalState, "save", unexpected_save)
        monkeypatch.setattr(click, "prompt", unexpected_prompt)
        monkeypatch.setattr(click, "confirm", unexpected_prompt)

        result = runner.invoke(
            cli,
            [
                "chapter",
                "approve",
                "--chapter",
                "6",
                "--audit-file",
                str(audit_path),
                "--revision-file",
                str(revision_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        after_state = json.loads(
            json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
        )
        after_files = _project_files()

        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "chapter": 6,
            "status": "conditionally_approved",
            "reason": "audit failed, but revision addressed 1 issues",
            "conditions": ["confirm continuity-gap remains resolved before snapshot"],
        }
        assert after_state == before_state
        assert after_files == before_files, (
            "approve must stay output-only; settle/postcheck/LLM/interactive approval remain deferred downstream steps"
        )


def test_route_returns_plain_text_for_pass_action() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(1)
        audit_path = _write_audit_file(
            {
                "chapter": 1,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issues": [],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "route",
                "--chapter",
                "1",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert result.output == (
            "Chapter: 1\nAction: pass\nReason: audit passed with no blocking issues\n"
        )


def test_route_returns_json_for_revise_action() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(2)
        audit_path = _write_audit_file(
            {
                "chapter": 2,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "route",
                "--chapter",
                "2",
                "--audit-file",
                str(audit_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "action": "revise",
            "reason": "audit failed with major severity",
            "audit_summary": {
                "chapter": 2,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issue_count": 1,
                "blocker_issue_count": 0,
            },
        }


def test_route_rejects_non_object_audit_file() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(1)
        audit_path = Path("audit.json")
        audit_path.write_text("[]", encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "--json",
                "chapter",
                "route",
                "--chapter",
                "1",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert json.loads(result.output) == {
            "error": "audit file must decode to a JSON object",
            "code": 1,
        }


def test_route_rejects_audit_file_for_different_chapter() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(1)
        audit_path = _write_audit_file(
            {
                "chapter": 2,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issues": [],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "route",
                "--chapter",
                "1",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert (
            result.output
            == "Error: audit file chapter '2' does not match --chapter '1'\n"
        )


def test_route_returns_non_zero_for_rewrite_action() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(3)
        audit_path = _write_audit_file(
            {
                "chapter": 3,
                "status": "fail",
                "severity": "blocker",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "timeline-break",
                        "severity": "blocker",
                        "message": "chapter breaks chronology",
                        "location": {"line": 8, "start": 0, "end": 10, "excerpt": ""},
                    }
                ],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "route",
                "--chapter",
                "3",
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "Action: rewrite" in result.output
        assert (
            "Reason: audit failed with blocker severity across 1 blocker issues"
            in result.output
        )


def test_route_returns_non_zero_for_escalate_action() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(4)
        audit_path = _write_audit_file(
            {
                "chapter": 4,
                "status": "fail",
                "severity": "blocker",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "timeline-break",
                        "severity": "blocker",
                        "message": "chapter breaks chronology",
                        "location": {"line": 1, "start": 0, "end": 10, "excerpt": ""},
                    },
                    {
                        "rule": "identity-break",
                        "severity": "blocker",
                        "message": "chapter changes a protagonist identity",
                        "location": {"line": 2, "start": 0, "end": 10, "excerpt": ""},
                    },
                    {
                        "rule": "setting-break",
                        "severity": "blocker",
                        "message": "chapter moves a location off-canon",
                        "location": {"line": 3, "start": 0, "end": 10, "excerpt": ""},
                    },
                ],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "route",
                "--chapter",
                "4",
                "--audit-file",
                str(audit_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert json.loads(result.output) == {
            "action": "escalate",
            "reason": "audit failed with 3 blocker issues and requires escalation",
            "audit_summary": {
                "chapter": 4,
                "status": "fail",
                "severity": "blocker",
                "recommended_action": "revise_chapter",
                "issue_count": 3,
                "blocker_issue_count": 3,
            },
        }


def test_revise_returns_plain_text_and_writes_revised_file() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(2)
        text_path = _write_text_file("chapter_2.md", "Scene text.")
        audit_path = _write_audit_file(
            {
                "chapter": 2,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "2",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        revised_path = Path("chapters") / "chapter_2_revised.md"
        assert result.exit_code == 0
        assert result.output == (
            "Chapter: 2\n"
            "Action: revise\n"
            "Issues addressed: 1\n"
            f"Output path: {revised_path.resolve()}\n"
        )
        assert revised_path.read_text(encoding="utf-8") == (
            "Scene text.\n<!-- REVISION NOTE: continuity-gap - chapter contradicts prior event -->"
        )


def test_revise_keeps_canonical_state_output_only_and_skips_downstream_paths(
    monkeypatch,
) -> None:
    from novel_cli.commands import chapter as chapter_commands

    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(6)
        text_path = _write_text_file("chapter_6.md", "Guardrail scene.")
        audit_path = _write_audit_file(
            {
                "chapter": 6,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "continuity-gap",
                        "severity": "major",
                        "message": "chapter contradicts prior event",
                        "location": {"line": 4, "start": 0, "end": 12, "excerpt": ""},
                    }
                ],
            }
        )
        before_state = json.loads(
            json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
        )
        before_files = _project_files()

        class UnexpectedSettler:
            def __init__(self, *args, **kwargs) -> None:
                raise AssertionError(
                    "revise must not invoke settle; that remains deferred"
                )

        class UnexpectedPostcheckRunner:
            def __init__(self, *args, **kwargs) -> None:
                raise AssertionError(
                    "revise must not invoke postcheck; that remains deferred"
                )

        def unexpected_save(self, project_dir: Path) -> None:
            raise AssertionError("revise must not save canonical state")

        monkeypatch.setattr(chapter_commands, "ChapterSettler", UnexpectedSettler)
        monkeypatch.setattr(
            chapter_commands, "PostcheckRunner", UnexpectedPostcheckRunner
        )
        monkeypatch.setattr(CanonicalState, "save", unexpected_save)

        result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "6",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        revised_path = Path("chapters") / "chapter_6_revised.md"
        after_state = json.loads(
            json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
        )
        after_files = _project_files()

        assert result.exit_code == 0
        assert after_state == before_state
        assert revised_path.is_file()
        assert after_files - before_files == {"chapters/chapter_6_revised.md"}, (
            "revise must stay output-only; approve/export/settle/postcheck remain deferred downstream steps"
        )
        assert not any("approve" in path for path in after_files - before_files)
        assert not any("export" in path for path in after_files - before_files)


def test_revise_returns_json_and_structured_revision_payload() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(5)
        text_path = _write_text_file("chapter_5.md", "Draft scene.")
        audit_path = _write_audit_file(
            {
                "chapter": 5,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "motivation-gap",
                        "severity": "major",
                        "message": "motivation is unclear",
                        "location": {"line": 7, "start": 0, "end": 15, "excerpt": ""},
                    }
                ],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "5",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(audit_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "chapter": 5,
            "path": str((Path.cwd() / "chapters" / "chapter_5_revised.md").resolve()),
            "revised_text": "Draft scene.\n<!-- REVISION NOTE: motivation-gap - motivation is unclear -->",
            "revision_log": [
                "<!-- REVISION NOTE: motivation-gap - motivation is unclear -->"
            ],
            "issues_addressed": [
                {
                    "rule": "motivation-gap",
                    "severity": "major",
                    "message": "motivation is unclear",
                    "location": {"line": 7, "start": 0, "end": 15, "excerpt": ""},
                }
            ],
            "routing_action": "revise",
        }


def test_revise_rejects_audit_file_for_different_chapter_json_output() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(5)
        text_path = _write_text_file("chapter_5.md", "Draft scene.")
        audit_path = _write_audit_file(
            {
                "chapter": 4,
                "status": "fail",
                "severity": "major",
                "recommended_action": "revise_chapter",
                "issues": [],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "5",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(audit_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert json.loads(result.output) == {
            "error": "audit file chapter '4' does not match --chapter '5'",
            "code": 1,
        }
        assert not (Path("chapters") / "chapter_5_revised.md").exists()


def test_revise_returns_no_revision_needed_for_pass_action() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(1)
        text_path = _write_text_file("chapter_1.md", "Clean text.")
        audit_path = _write_audit_file(
            {
                "chapter": 1,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issues": [],
            }
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "1",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert result.output == "No revision needed for chapter 1\n"
        assert not (Path("chapters") / "chapter_1_revised.md").exists()


def test_revise_pass_keeps_canonical_state_and_project_files_unchanged() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(7)
        text_path = _write_text_file("chapter_7.md", "Clean text.")
        audit_path = _write_audit_file(
            {
                "chapter": 7,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issues": [],
            }
        )
        before_state = json.loads(
            json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
        )
        before_files = _project_files()

        result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "7",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(audit_path),
            ],
            catch_exceptions=False,
        )

        after_state = json.loads(
            json.dumps(CanonicalState.load(Path.cwd()).data, sort_keys=True)
        )

        assert result.exit_code == 0
        assert result.output == "No revision needed for chapter 7\n"
        assert after_state == before_state
        assert _project_files() == before_files


def test_revise_returns_non_zero_and_skips_file_write_for_non_revise_actions() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _save_state_with_chapter(4)
        text_path = _write_text_file("chapter_4.md", "Blocked text.")
        rewrite_path = _write_audit_file(
            {
                "chapter": 4,
                "status": "fail",
                "severity": "blocker",
                "recommended_action": "revise_chapter",
                "issues": [
                    {
                        "rule": "timeline-break",
                        "severity": "blocker",
                        "message": "chapter breaks chronology",
                        "location": {"line": 8, "start": 0, "end": 10, "excerpt": ""},
                    }
                ],
            }
        )

        rewrite_result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "4",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(rewrite_path),
            ],
            catch_exceptions=False,
        )

        assert rewrite_result.exit_code == 1
        assert "Action: rewrite" in rewrite_result.output
        assert not (Path("chapters") / "chapter_4_revised.md").exists()

        escalate_path = Path("audit-escalate.json")
        escalate_path.write_text(
            json.dumps(
                {
                    "chapter": 4,
                    "status": "fail",
                    "severity": "blocker",
                    "recommended_action": "revise_chapter",
                    "issues": [
                        {
                            "rule": "timeline-break",
                            "severity": "blocker",
                            "message": "chapter breaks chronology",
                            "location": {
                                "line": 1,
                                "start": 0,
                                "end": 10,
                                "excerpt": "",
                            },
                        },
                        {
                            "rule": "identity-break",
                            "severity": "blocker",
                            "message": "chapter changes a protagonist identity",
                            "location": {
                                "line": 2,
                                "start": 0,
                                "end": 10,
                                "excerpt": "",
                            },
                        },
                        {
                            "rule": "setting-break",
                            "severity": "blocker",
                            "message": "chapter moves a location off-canon",
                            "location": {
                                "line": 3,
                                "start": 0,
                                "end": 10,
                                "excerpt": "",
                            },
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        escalate_result = runner.invoke(
            cli,
            [
                "chapter",
                "revise",
                "--chapter",
                "4",
                "--text-file",
                str(text_path),
                "--audit-file",
                str(escalate_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        assert escalate_result.exit_code == 1
        assert json.loads(escalate_result.output) == {
            "action": "escalate",
            "reason": "audit failed with 3 blocker issues and requires escalation",
            "audit_summary": {
                "chapter": 4,
                "status": "fail",
                "severity": "blocker",
                "recommended_action": "revise_chapter",
                "issue_count": 3,
                "blocker_issue_count": 3,
            },
        }
        assert not (Path("chapters") / "chapter_4_revised.md").exists()


def test_draft_creates_runtime_backed_file() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
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
        state.save(Path.cwd())

        result = runner.invoke(
            cli, ["chapter", "draft", "--chapter", "2"], catch_exceptions=False
        )

        assert result.exit_code == 0
        chapter_path = Path("chapters") / "chapter_2.md"
        assert result.output == f"Drafted chapter 2 at {chapter_path.resolve()}\n"
        assert chapter_path.is_file()
        assert chapter_path.read_text(encoding="utf-8") == (
            "# Chapter 2\n\nMira takes the next step.\n"
        )

        state = CanonicalState.load(Path.cwd())
        assert state.data["chapters"] == [
            {
                "number": 2,
                "title": "Chapter 2",
                "status": "draft",
                "summary": "Mira takes the next step.",
                "settled_at": "",
            }
        ]


def test_draft_json_output_matches_runtime_contract() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
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
        state.save(Path.cwd())

        result = runner.invoke(
            cli,
            ["chapter", "draft", "--chapter", "3", "--json"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {
            "chapter": 3,
            "title": "Chapter 3",
            "status": "draft",
            "summary": "Mira takes the next step.",
            "path": str((Path.cwd() / "chapters" / "chapter_3.md").resolve()),
        }

        chapter_path = Path(payload["path"])
        assert chapter_path.name == "chapter_3.md"
        assert chapter_path.read_text(encoding="utf-8") == (
            "# Chapter 3\n\nMira takes the next step.\n"
        )

        state = CanonicalState.load(Path.cwd())
        assert state.data["chapters"] == [
            {
                "number": 3,
                "title": "Chapter 3",
                "status": "draft",
                "summary": "Mira takes the next step.",
                "settled_at": "",
            }
        ]


def test_draft_resets_settled_at_when_redrafting_settled_chapter() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
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
        state.data["chapters"].append(
            {
                "number": 1,
                "title": "Arrival",
                "status": "settled",
                "summary": "Old settled summary.",
                "settled_at": "2026-03-22T12:34:56Z",
            }
        )
        state.save(Path.cwd())

        result = runner.invoke(
            cli, ["chapter", "draft", "--chapter", "1"], catch_exceptions=False
        )

        assert result.exit_code == 0
        chapter_path = Path("chapters") / "chapter_1.md"
        assert result.output == f"Drafted chapter 1 at {chapter_path.resolve()}\n"

        state = CanonicalState.load(Path.cwd())
        assert state.data["chapters"] == [
            {
                "number": 1,
                "title": "Chapter 1",
                "status": "draft",
                "summary": "Mira takes the next step.",
                "settled_at": "",
            }
        ]


def test_draft_requires_active_world_entity_plain_output() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())

        result = runner.invoke(
            cli, ["chapter", "draft", "--chapter", "1"], catch_exceptions=False
        )

        assert result.exit_code == 1
        assert (
            result.output
            == "Error: chapter 1 draft requires at least one active world entity\n"
        )


def test_draft_requires_active_world_entity_json_output() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())

        result = runner.invoke(
            cli,
            ["--json", "chapter", "draft", "--chapter", "1"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert json.loads(result.output) == {
            "error": "chapter 1 draft requires at least one active world entity",
            "code": 1,
        }


def test_draft_failure_without_selected_project_json_output() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["--json", "chapter", "draft", "--chapter", "1"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert json.loads(result.output) == {
            "error": "no novel project selected",
            "code": 1,
        }


def test_settle_updates_state() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
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
        state.data["chapters"].append(
            {
                "number": 1,
                "title": "Arrival",
                "status": "draft",
                "summary": "Mira approaches the vault.",
                "settled_at": "",
            }
        )
        state.save(Path.cwd())

        settlement_path = Path("settlement.json")
        settlement_path.write_text(
            json.dumps(
                {
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
                            "attributes": {
                                "role": "lead",
                                "location": "Sunspire Vault",
                            },
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
                    "foreshadow_updates": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        chapter_text_path = Path("chapter_1.md")
        chapter_text_path.write_text("Mira reached the vault.", encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "chapter",
                "settle",
                "--chapter",
                "1",
                "--settlement-file",
                str(settlement_path),
                "--text-file",
                str(chapter_text_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        updated_state = CanonicalState.load(Path.cwd())
        assert updated_state.data["chapters"][0]["status"] == "settled"
        assert (
            updated_state.data["chapters"][0]["summary"] == "Mira approaches the vault."
        )
        assert updated_state.data["chapters"][0]["settled_at"]
        assert updated_state.data["world"]["entities"][-1]["name"] == "Sunspire Vault"
        assert updated_state.data["timeline"]["events"][0]["chapter"] == 1


def test_postcheck_returns_result() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        state = CanonicalState.create_empty("mybook", "fantasy")
        state.data["world"]["entities"].extend(
            [
                {
                    "id": "entity-1",
                    "name": "Mira",
                    "type": "character",
                    "attributes": {},
                    "visibility": "active",
                },
                {
                    "id": "entity-2",
                    "name": "Shade",
                    "type": "character",
                    "attributes": {},
                    "visibility": "hidden",
                },
            ]
        )
        state.data["chapters"].append(
            {
                "number": 1,
                "title": "Arrival",
                "status": "draft",
                "summary": "Mira enters the city.",
                "settled_at": "",
            }
        )
        state.save(Path.cwd())
        text_path = Path("chapter_1.md")
        text_path.write_text(
            "Mira spotted Shade in the tower window.", encoding="utf-8"
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "postcheck",
                "--chapter",
                "1",
                "--text-file",
                str(text_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Passed: no" in result.output
        assert "hidden-entity-appearance | blocker" in result.output


def test_postcheck_json_output() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        state = CanonicalState.create_empty("mybook", "fantasy")
        state.data["chapters"].append(
            {
                "number": 1,
                "title": "Arrival",
                "status": "draft",
                "summary": "Quiet road.",
                "settled_at": "",
            }
        )
        state.save(Path.cwd())
        text_path = Path("chapter_1.md")
        text_path.write_text(
            "A quiet road stretched toward the hills.", encoding="utf-8"
        )

        result = runner.invoke(
            cli,
            [
                "chapter",
                "postcheck",
                "--chapter",
                "1",
                "--text-file",
                str(text_path),
                "--json",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["chapter"] == 1
        assert payload["passed"] is True
        assert payload["issues"] == [
            {
                "rule": "world-model-missing",
                "severity": "minor",
                "message": "world model is empty; entity-based checks were skipped",
                "location": {"line": 1, "start": 0, "end": 0, "excerpt": ""},
            }
        ]


def _save_state_with_chapter(chapter_number: int) -> None:
    state = CanonicalState.create_empty("mybook", "fantasy")
    state.data["chapters"].append(
        {
            "number": chapter_number,
            "title": f"Chapter {chapter_number}",
            "status": "draft",
            "summary": "Summary.",
            "settled_at": "",
        }
    )
    state.save(Path.cwd())


def _write_audit_file(payload: dict[str, object]) -> Path:
    audit_path = Path("audit.json")
    audit_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return audit_path


def _write_revision_file(payload: dict[str, object]) -> Path:
    revision_path = Path("revision.json")
    revision_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return revision_path


def _write_text_file(name: str, content: str) -> Path:
    path = Path(name)
    path.write_text(content, encoding="utf-8")
    return path


def _project_files() -> set[str]:
    return {
        path.relative_to(Path.cwd()).as_posix()
        for path in Path.cwd().rglob("*")
        if path.is_file()
    }
