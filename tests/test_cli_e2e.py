import json
from pathlib import Path

from click.testing import CliRunner
from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.snapshot import SnapshotManager

from novel_cli.main import cli


def _assert_current_chapter_surface(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["chapter", "--help"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "draft" in result.output
    assert "settle" in result.output
    assert "postcheck" in result.output
    assert "audit" in result.output
    assert "route" in result.output
    assert "revise" in result.output
    assert "approve" in result.output


def test_chapter_full_lifecycle() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _assert_current_chapter_surface(runner)
        init_result = runner.invoke(
            cli,
            ["project", "init", "mybook", "--genre", "fantasy"],
            catch_exceptions=False,
        )
        add_result = runner.invoke(
            cli,
            [
                "world",
                "entity",
                "add",
                "--name",
                "Kai",
                "--type",
                "character",
                "--attributes",
                '{"role": "lead"}',
            ],
            catch_exceptions=False,
        )
        draft_result = runner.invoke(
            cli, ["chapter", "draft", "--chapter", "1"], catch_exceptions=False
        )

        project_dir = Path("mybook")
        chapter_text_path = project_dir / "chapters" / "chapter_1.md"
        expected_draft_path = chapter_text_path.resolve()
        expected_summary = "Kai takes the next step."
        expected_draft_text = f"# Chapter 1\n\n{expected_summary}\n"
        drafted_text = chapter_text_path.read_text(encoding="utf-8")
        chapter_text_path.write_text(
            "Kai reaches the Archive at dawn.", encoding="utf-8"
        )
        settlement_path = Path("settlement.json")
        settlement_path.write_text(
            json.dumps(
                {
                    "new_entities": [
                        {
                            "id": "entity-2",
                            "name": "Archive",
                            "type": "location",
                            "attributes": {"kind": "library"},
                            "visibility": "reference",
                        }
                    ],
                    "updated_entities": [
                        {
                            "id": "entity-1",
                            "attributes": {
                                "role": "lead",
                                "location": "Archive",
                            },
                        }
                    ],
                    "new_relationships": [
                        {
                            "source": "entity-1",
                            "target": "entity-2",
                            "type": "arrives-at",
                            "since_chapter": 1,
                        }
                    ],
                    "events": [
                        {
                            "chapter": 1,
                            "type": "arrival",
                            "summary": "Kai arrives at the Archive.",
                            "entities": ["entity-1", "entity-2"],
                        }
                    ],
                    "foreshadow_updates": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        settle_result = runner.invoke(
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
        postcheck_result = runner.invoke(
            cli,
            [
                "chapter",
                "postcheck",
                "--chapter",
                "1",
                "--text-file",
                str(chapter_text_path),
            ],
            catch_exceptions=False,
        )
        audit_payload = _invoke_json(
            runner,
            [
                "chapter",
                "audit",
                "--chapter",
                "1",
                "--text-file",
                str(chapter_text_path),
            ],
        )
        audit_path = Path("audit.json")
        audit_path.write_text(
            json.dumps(audit_payload, ensure_ascii=False), encoding="utf-8"
        )
        route_payload = _invoke_json(
            runner,
            [
                "chapter",
                "route",
                "--chapter",
                "1",
                "--audit-file",
                str(audit_path),
            ],
        )
        revise_payload = _invoke_json(
            runner,
            [
                "chapter",
                "revise",
                "--chapter",
                "1",
                "--text-file",
                str(chapter_text_path),
                "--audit-file",
                str(audit_path),
            ],
        )
        approve_result = runner.invoke(
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
        snapshot_result = runner.invoke(
            cli,
            ["snapshot", "create", "--label", "full-lifecycle"],
            catch_exceptions=False,
        )
        state_result = runner.invoke(cli, ["state", "show"], catch_exceptions=False)

        for result in (
            init_result,
            add_result,
            draft_result,
            settle_result,
            postcheck_result,
            approve_result,
            snapshot_result,
            state_result,
        ):
            assert result.exit_code == 0

        assert "Initialized project 'mybook'" in init_result.output
        assert "Added entity 'Kai' (entity-1)" in add_result.output
        assert draft_result.output.strip() == (
            f"Drafted chapter 1 at {expected_draft_path}"
        )
        assert drafted_text == expected_draft_text
        assert "Settled chapter 1" in settle_result.output
        assert "Passed: yes" in postcheck_result.output
        assert audit_payload == {
            "chapter": 1,
            "status": "pass",
            "severity": "none",
            "recommended_action": "proceed_to_snapshot",
            "issues": [],
        }
        assert route_payload == {
            "action": "pass",
            "reason": "audit passed with no blocking issues",
            "audit_summary": {
                "chapter": 1,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issue_count": 0,
                "blocker_issue_count": 0,
            },
        }
        assert revise_payload == {
            "chapter": 1,
            "routing_action": "pass",
            "reason": "audit passed with no blocking issues",
        }
        assert approve_result.output == (
            "Chapter: 1\n"
            "Status: approved\n"
            "Reason: audit passed and chapter is ready for snapshot\n"
            "Conditions: none\n"
        )
        assert "Created snapshot '" in snapshot_result.output
        assert not (project_dir / "chapters" / "chapter_1_revised.md").exists()

        state_payload = json.loads(state_result.output)
        entities = state_payload["world"]["entities"]
        chapters = state_payload["chapters"]
        assert [entity["name"] for entity in entities] == ["Kai", "Archive"]
        assert entities[0]["attributes"]["location"] == "Archive"
        assert chapters == [
            {
                "number": 1,
                "title": "Chapter 1",
                "status": "settled",
                "summary": expected_summary,
                "settled_at": chapters[0]["settled_at"],
            }
        ]
        assert chapters[0]["settled_at"]
        assert state_payload["timeline"]["events"] == [
            {
                "chapter": 1,
                "type": "arrival",
                "summary": "Kai arrives at the Archive.",
                "entities": ["entity-1", "entity-2"],
            }
        ]

        snapshots = SnapshotManager(project_dir).list_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0]["id"]
        assert snapshots[0]["label"] == "full-lifecycle"
        snapshot_state = (
            SnapshotManager(project_dir).load_snapshot(snapshots[0]["id"]).data
        )
        assert snapshot_state["chapters"] == chapters
        assert snapshot_state["timeline"] == state_payload["timeline"]


def test_chapter_full_lifecycle_json_mode() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _assert_current_chapter_surface(runner)
        init_payload = _invoke_json(
            runner, ["project", "init", "mybook", "--genre", "fantasy"]
        )
        add_payload = _invoke_json(
            runner,
            [
                "world",
                "entity",
                "add",
                "--name",
                "Kai",
                "--type",
                "character",
                "--attributes",
                '{"role": "lead"}',
            ],
        )
        draft_payload = _invoke_json(runner, ["chapter", "draft", "--chapter", "1"])

        project_dir = Path("mybook")
        chapter_text_path = project_dir / "chapters" / "chapter_1.md"
        expected_draft_path = chapter_text_path.resolve()
        expected_summary = "Kai takes the next step."
        expected_draft_text = f"# Chapter 1\n\n{expected_summary}\n"
        assert chapter_text_path.read_text(encoding="utf-8") == expected_draft_text
        chapter_text_path.write_text(
            "Kai reaches the Archive at dawn.", encoding="utf-8"
        )
        settlement_path = Path("settlement.json")
        settlement_path.write_text(
            json.dumps(
                {
                    "new_entities": [
                        {
                            "id": "entity-2",
                            "name": "Archive",
                            "type": "location",
                            "attributes": {"kind": "library"},
                            "visibility": "reference",
                        }
                    ],
                    "updated_entities": [
                        {
                            "id": "entity-1",
                            "attributes": {
                                "role": "lead",
                                "location": "Archive",
                            },
                        }
                    ],
                    "new_relationships": [
                        {
                            "source": "entity-1",
                            "target": "entity-2",
                            "type": "arrives-at",
                            "since_chapter": 1,
                        }
                    ],
                    "events": [
                        {
                            "chapter": 1,
                            "type": "arrival",
                            "summary": "Kai arrives at the Archive.",
                            "entities": ["entity-1", "entity-2"],
                        }
                    ],
                    "foreshadow_updates": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        settle_payload = _invoke_json(
            runner,
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
        )
        postcheck_payload = _invoke_json(
            runner,
            [
                "chapter",
                "postcheck",
                "--chapter",
                "1",
                "--text-file",
                str(chapter_text_path),
            ],
        )
        audit_payload = _invoke_json(
            runner,
            [
                "chapter",
                "audit",
                "--chapter",
                "1",
                "--text-file",
                str(chapter_text_path),
            ],
        )
        audit_path = Path("audit.json")
        audit_path.write_text(
            json.dumps(audit_payload, ensure_ascii=False), encoding="utf-8"
        )
        route_payload = _invoke_json(
            runner,
            [
                "chapter",
                "route",
                "--chapter",
                "1",
                "--audit-file",
                str(audit_path),
            ],
        )
        revise_payload = _invoke_json(
            runner,
            [
                "chapter",
                "revise",
                "--chapter",
                "1",
                "--text-file",
                str(chapter_text_path),
                "--audit-file",
                str(audit_path),
            ],
        )
        approve_payload = _invoke_json(
            runner,
            [
                "chapter",
                "approve",
                "--chapter",
                "1",
                "--audit-file",
                str(audit_path),
            ],
        )
        snapshot_payload = _invoke_json(
            runner, ["snapshot", "create", "--label", "full-lifecycle"]
        )
        state_payload = _invoke_json(runner, ["state", "show"])

        assert init_payload["name"] == "mybook"
        assert init_payload["genre"] == "fantasy"
        assert add_payload["entity"] == {
            "id": "entity-1",
            "name": "Kai",
            "type": "character",
            "attributes": {"role": "lead"},
            "visibility": "active",
        }
        assert draft_payload == {
            "chapter": 1,
            "title": "Chapter 1",
            "status": "draft",
            "path": str(expected_draft_path),
            "summary": expected_summary,
        }
        assert settle_payload == {"chapter": 1, "status": "settled"}
        assert postcheck_payload == {"chapter": 1, "passed": True, "issues": []}
        assert audit_payload == {
            "chapter": 1,
            "status": "pass",
            "severity": "none",
            "recommended_action": "proceed_to_snapshot",
            "issues": [],
        }
        assert route_payload == {
            "action": "pass",
            "reason": "audit passed with no blocking issues",
            "audit_summary": {
                "chapter": 1,
                "status": "pass",
                "severity": "none",
                "recommended_action": "proceed_to_snapshot",
                "issue_count": 0,
                "blocker_issue_count": 0,
            },
        }
        assert revise_payload == {
            "chapter": 1,
            "routing_action": "pass",
            "reason": "audit passed with no blocking issues",
        }
        assert approve_payload == {
            "chapter": 1,
            "status": "approved",
            "reason": "audit passed and chapter is ready for snapshot",
            "conditions": [],
        }

        snapshot = snapshot_payload["snapshot"]
        assert snapshot["id"]
        assert snapshot["label"] == "full-lifecycle"
        assert snapshot["timestamp"]
        assert not (project_dir / "chapters" / "chapter_1_revised.md").exists()

        state = state_payload["state"]
        assert state["project"] == CanonicalState.load(project_dir).data["project"]
        assert state["world"]["entities"] == [
            {
                "id": "entity-1",
                "name": "Kai",
                "type": "character",
                "attributes": {"role": "lead", "location": "Archive"},
                "visibility": "active",
            },
            {
                "id": "entity-2",
                "name": "Archive",
                "type": "location",
                "attributes": {"kind": "library"},
                "visibility": "reference",
            },
        ]
        assert state["chapters"][0]["number"] == 1
        assert state["chapters"][0]["status"] == "settled"
        assert state["chapters"][0]["summary"] == expected_summary
        assert state["chapters"][0]["settled_at"]
        assert state["timeline"]["events"] == [
            {
                "chapter": 1,
                "type": "arrival",
                "summary": "Kai arrives at the Archive.",
                "entities": ["entity-1", "entity-2"],
            }
        ]
        snapshot_state = SnapshotManager(project_dir).load_snapshot(snapshot["id"]).data
        assert snapshot_state["chapters"] == state["chapters"]
        assert snapshot_state["timeline"] == state["timeline"]


def _invoke_json(runner: CliRunner, args: list[str]) -> dict:
    result = runner.invoke(cli, ["--json", *args], catch_exceptions=False)
    assert result.exit_code == 0
    return json.loads(result.output)
