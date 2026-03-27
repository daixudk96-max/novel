# pyright: reportMissingImports=false

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
    assert "guide" in result.output
    assert "verify-guided-result" in result.output
    assert "settle" in result.output
    assert "postcheck" in result.output
    assert "audit" in result.output
    assert "route" in result.output
    assert "revise" in result.output
    assert "approve" in result.output


def test_chapter_full_lifecycle(monkeypatch) -> None:
    from novel_cli.commands import chapter as chapter_commands

    runner = CliRunner()

    with runner.isolated_filesystem():
        monkeypatch.setattr(
            chapter_commands, "build_route_a_provider", lambda: _E2EFakeDraftProvider()
        )
        monkeypatch.setenv("NOVEL_LLM_PROVIDER", "openai")
        monkeypatch.setenv("NOVEL_LLM_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("NOVEL_LLM_API_KEY", "test-key")
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


def test_chapter_full_lifecycle_json_mode(monkeypatch) -> None:
    from novel_cli.commands import chapter as chapter_commands

    runner = CliRunner()

    with runner.isolated_filesystem():
        monkeypatch.setattr(
            chapter_commands, "build_route_a_provider", lambda: _E2EFakeDraftProvider()
        )
        monkeypatch.setenv("NOVEL_LLM_PROVIDER", "openai")
        monkeypatch.setenv("NOVEL_LLM_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("NOVEL_LLM_API_KEY", "test-key")
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


# verification selector: def test_chapter_draft_retry_recovery_preserves_single_write|def test_chapter_draft_retry_exhaustion_leaves_no_partial_side_effects
def test_chapter_draft_retry_recovery_preserves_single_write(monkeypatch) -> None:
    from novel_cli.commands import chapter as chapter_commands

    runner = CliRunner()
    original_upsert = chapter_commands._upsert_chapter
    original_save = CanonicalState.save
    original_write_text = Path.write_text

    with runner.isolated_filesystem():
        _save_route_a_project()
        counts = {"upsert": 0, "save": 0, "chapter_write": 0}
        provider = _RetryThenSuccessDraftProvider()

        def tracked_upsert(state, draft):
            counts["upsert"] += 1
            return original_upsert(state, draft)

        def tracked_save(self, project_dir: Path):
            counts["save"] += 1
            return original_save(self, project_dir)

        def tracked_write_text(path: Path, data: str, *args, **kwargs):
            if path.name == "chapter_1.md":
                counts["chapter_write"] += 1
            return original_write_text(path, data, *args, **kwargs)

        monkeypatch.setattr(
            chapter_commands, "build_route_a_provider", lambda: provider
        )
        monkeypatch.setattr(chapter_commands, "_upsert_chapter", tracked_upsert)
        monkeypatch.setattr(CanonicalState, "save", tracked_save)
        monkeypatch.setattr(Path, "write_text", tracked_write_text)
        monkeypatch.setenv("NOVEL_LLM_PROVIDER", "openai")
        monkeypatch.setenv("NOVEL_LLM_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("NOVEL_LLM_API_KEY", "test-key")

        result = runner.invoke(
            cli, ["chapter", "draft", "--chapter", "1"], catch_exceptions=False
        )

        project_dir = Path.cwd()
        chapter_path = project_dir / "chapters" / "chapter_1.md"
        assert result.exit_code == 0
        assert provider.calls == 2
        assert counts == {"upsert": 1, "save": 1, "chapter_write": 1}
        assert chapter_path.read_text(encoding="utf-8") == "Recovered after retry."
        assert CanonicalState.load(project_dir).data["chapters"] == [
            {
                "number": 1,
                "title": "Chapter 1",
                "status": "draft",
                "summary": "Mira takes the next step.",
                "settled_at": "",
            }
        ]


def test_chapter_draft_retry_exhaustion_leaves_no_partial_side_effects(
    monkeypatch,
) -> None:
    from novel_cli.commands import chapter as chapter_commands

    runner = CliRunner()
    original_upsert = chapter_commands._upsert_chapter
    original_save = CanonicalState.save
    original_write_text = Path.write_text

    with runner.isolated_filesystem():
        _save_route_a_project()
        counts = {"upsert": 0, "save": 0, "chapter_write": 0}
        provider = _AlwaysRetryableDraftProvider()

        def tracked_upsert(state, draft):
            counts["upsert"] += 1
            return original_upsert(state, draft)

        def tracked_save(self, project_dir: Path):
            counts["save"] += 1
            return original_save(self, project_dir)

        def tracked_write_text(path: Path, data: str, *args, **kwargs):
            if path.name == "chapter_1.md":
                counts["chapter_write"] += 1
            return original_write_text(path, data, *args, **kwargs)

        monkeypatch.setattr(
            chapter_commands, "build_route_a_provider", lambda: provider
        )
        monkeypatch.setattr(chapter_commands, "_upsert_chapter", tracked_upsert)
        monkeypatch.setattr(CanonicalState, "save", tracked_save)
        monkeypatch.setattr(Path, "write_text", tracked_write_text)
        monkeypatch.setenv("NOVEL_LLM_PROVIDER", "openai")
        monkeypatch.setenv("NOVEL_LLM_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("NOVEL_LLM_API_KEY", "test-key")

        result = runner.invoke(
            cli,
            ["--json", "chapter", "draft", "--chapter", "1"],
            catch_exceptions=False,
        )

        project_dir = Path.cwd()
        assert result.exit_code == 1
        assert provider.calls == 3
        assert json.loads(result.output) == {
            "error": "chapter draft failed after 3 attempts: retry later",
            "code": 1,
        }
        assert counts == {"upsert": 0, "save": 0, "chapter_write": 0}
        assert not (project_dir / "chapters" / "chapter_1.md").exists()
        assert CanonicalState.load(project_dir).data["chapters"] == []


def test_route_b_guided_flow_without_llm_env(monkeypatch) -> None:
    from novel_cli.commands import chapter as chapter_commands

    runner = CliRunner()

    with runner.isolated_filesystem():
        _clear_llm_env(monkeypatch)
        _assert_current_chapter_surface(runner)

        def unexpected_route_a_usage(*args, **kwargs):
            raise AssertionError("Route B flow must not call chapter draft")

        monkeypatch.setattr(
            chapter_commands, "build_route_a_provider", unexpected_route_a_usage
        )
        monkeypatch.setattr(
            chapter_commands, "_build_chapter_drafter", unexpected_route_a_usage
        )

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
        guide_payload = _invoke_json(runner, ["chapter", "guide", "--chapter", "1"])

        project_dir = Path("mybook")
        manifest_path, prose_path, settlement_path = _write_guided_result_artifacts(
            chapter_number=1
        )

        assert guide_payload["recommended_action"] == "chapter verify-guided-result"
        verify_payload = _invoke_json(
            runner,
            [
                "chapter",
                "verify-guided-result",
                "--chapter",
                "1",
                "--manifest-file",
                str(manifest_path),
            ],
        )
        assert verify_payload["recommended_action"] == "chapter settle"

        settle_payload = _invoke_json(
            runner,
            [
                "chapter",
                "settle",
                "--chapter",
                "1",
                "--settlement-file",
                verify_payload["data"]["settlement_path"],
                "--text-file",
                verify_payload["data"]["prose_path"],
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
                str(prose_path),
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
                str(prose_path),
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
                str(prose_path),
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
            runner, ["snapshot", "create", "--label", "route-b-guided"]
        )
        state_payload = _invoke_json(runner, ["state", "show"])

        assert init_payload["name"] == "mybook"
        assert add_payload["entity"] == {
            "id": "entity-1",
            "name": "Kai",
            "type": "character",
            "attributes": {"role": "lead"},
            "visibility": "active",
        }
        assert guide_payload["data"]["version"] == "route-b-guidance/v1"
        assert guide_payload["data"]["workflow_id"] == "chapter-guided-assistant-v1"
        assert guide_payload["data"]["allowed_operations"] == [
            "read_project_files",
            "write_text_artifact",
            "write_json_artifact",
            "invoke_published_cli_command",
            "capture_command_receipt",
            "bundle_named_outputs",
        ]
        assert verify_payload == {
            "ok": True,
            "command": "chapter verify-guided-result",
            "version": "novel-cli-agent/v1",
            "data": {
                "guidance_id": "guide-chapter-1-route-b-v1",
                "chapter": 1,
                "prose_path": str(prose_path.resolve()),
                "settlement_path": str(settlement_path.resolve()),
                "command_receipts": [],
                "warnings": [],
                "ready_for_cli_validation": True,
            },
            "warnings": [],
            "recommended_action": "chapter settle",
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
        assert snapshot["label"] == "route-b-guided"
        assert snapshot["timestamp"]
        assert not (project_dir / "chapters" / "chapter_1.md").exists()
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
        assert state["chapters"] == [
            {
                "number": 1,
                "title": "Chapter 1",
                "status": "settled",
                "summary": "",
                "settled_at": state["chapters"][0]["settled_at"],
            }
        ]
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


def test_route_b_guided_flow_rejects_validation_bypass(monkeypatch) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        _clear_llm_env(monkeypatch)
        _assert_current_chapter_surface(runner)

        _invoke_json(runner, ["project", "init", "mybook", "--genre", "fantasy"])
        _invoke_json(
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
        guide_payload = _invoke_json(runner, ["chapter", "guide", "--chapter", "1"])
        assert guide_payload["recommended_action"] == "chapter verify-guided-result"
        project_dir = Path("mybook")
        before_state = json.loads(
            json.dumps(CanonicalState.load(project_dir).data, sort_keys=True)
        )
        manifest_path, _, _ = _write_guided_result_artifacts(
            chapter_number=1,
            ready_for_cli_validation=False,
        )

        result = runner.invoke(
            cli,
            [
                "--json",
                "chapter",
                "verify-guided-result",
                "--chapter",
                "1",
                "--manifest-file",
                str(manifest_path),
            ],
            catch_exceptions=False,
        )

        after_state = json.loads(
            json.dumps(CanonicalState.load(project_dir).data, sort_keys=True)
        )

        assert result.exit_code == 1
        assert json.loads(result.output) == {
            "error": "manifest ready_for_cli_validation must be true",
            "code": 1,
        }
        assert after_state == before_state
        assert after_state["chapters"] == []


def _invoke_json(runner: CliRunner, args: list[str]) -> dict:
    result = runner.invoke(cli, ["--json", *args], catch_exceptions=False)
    assert result.exit_code == 0
    return json.loads(result.output)


def _clear_llm_env(monkeypatch) -> None:
    for name in (
        "NOVEL_LLM_PROVIDER",
        "NOVEL_LLM_MODEL",
        "NOVEL_LLM_API_KEY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


def _save_route_a_project() -> None:
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


def _write_guided_result_artifacts(
    *, chapter_number: int, ready_for_cli_validation: bool = True
) -> tuple[Path, Path, Path]:
    prose_path = (
        Path("artifacts") / f"chapter-{chapter_number}" / f"chapter-{chapter_number}.md"
    )
    prose_path.parent.mkdir(parents=True, exist_ok=True)
    prose_path.write_text("Kai reaches the Archive at dawn.", encoding="utf-8")

    settlement_path = (
        Path("artifacts")
        / f"chapter-{chapter_number}"
        / f"chapter-{chapter_number}.settlement.json"
    )
    settlement_path.write_text(
        json.dumps(
            {
                "chapter": chapter_number,
                "prose_path": prose_path.as_posix(),
                "summary": "",
                "continuity_notes": [],
                "open_questions": [],
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
                        "since_chapter": chapter_number,
                    }
                ],
                "events": [
                    {
                        "chapter": chapter_number,
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

    manifest_path = Path("assistant-result.json")
    manifest_path.write_text(
        json.dumps(
            {
                "guidance_id": f"guide-chapter-{chapter_number}-route-b-v1",
                "version": "assistant-result/v1",
                "chapter": chapter_number,
                "operations_performed": [
                    "read_project_files",
                    "write_text_artifact",
                    "write_json_artifact",
                    "bundle_named_outputs",
                ],
                "created_files": [prose_path.as_posix(), settlement_path.as_posix()],
                "prose_path": prose_path.as_posix(),
                "settlement_path": settlement_path.as_posix(),
                "command_receipts": [],
                "warnings": [],
                "ready_for_cli_validation": ready_for_cli_validation,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest_path, prose_path, settlement_path


class _E2EFakeDraftProvider:
    def draft(self, *, prompt: str, temperature: float) -> str:
        assert temperature == 1.0
        prefix = "Draft Chapter "
        summary_marker = ". Summary: "
        assert prompt.startswith(prefix)
        assert summary_marker in prompt
        header, summary = prompt.split(summary_marker, maxsplit=1)
        chapter_number, _, _ = header.removeprefix(prefix).partition(" about ")
        return f"# Chapter {chapter_number}\n\n{summary}\n"


class _RetryThenSuccessDraftProvider:
    def __init__(self) -> None:
        self.calls = 0

    def draft(self, *, prompt: str, temperature: float) -> str:
        self.calls += 1
        assert (
            prompt == "Draft Chapter 1 about Mira. Summary: Mira takes the next step."
        )
        assert temperature == 1.0
        if self.calls == 1:
            raise _RateLimitError("retry later")
        return "Recovered after retry."


class _AlwaysRetryableDraftProvider:
    def __init__(self) -> None:
        self.calls = 0

    def draft(self, *, prompt: str, temperature: float) -> str:
        self.calls += 1
        assert (
            prompt == "Draft Chapter 1 about Mira. Summary: Mira takes the next step."
        )
        assert temperature == 1.0
        raise _RateLimitError("retry later")


class _RateLimitError(Exception):
    status_code = 429
