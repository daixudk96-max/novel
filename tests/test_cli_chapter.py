import json
from pathlib import Path

from click.testing import CliRunner
from novel_runtime.state.canonical import CanonicalState

from novel_cli.main import cli


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
