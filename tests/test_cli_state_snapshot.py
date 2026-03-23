import json
from pathlib import Path

from click.testing import CliRunner
from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.snapshot import SnapshotManager

from novel_cli.main import cli


def test_state_show_empty_project_json() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        state = CanonicalState.create_empty("mybook", "fantasy")
        state.save(Path.cwd())

        result = runner.invoke(cli, ["state", "show", "--json"], catch_exceptions=False)

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {"state": state.data}


def test_snapshot_create_and_list() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())

        create_result = runner.invoke(
            cli,
            ["snapshot", "create", "--label", "baseline", "--json"],
            catch_exceptions=False,
        )
        list_result = runner.invoke(
            cli, ["snapshot", "list", "--json"], catch_exceptions=False
        )

        assert create_result.exit_code == 0
        assert list_result.exit_code == 0
        create_payload = json.loads(create_result.output)
        list_payload = json.loads(list_result.output)
        assert list_payload["count"] == 1
        assert list_payload["snapshots"] == [
            {
                "id": create_payload["snapshot"]["id"],
                "timestamp": create_payload["snapshot"]["timestamp"],
                "label": "baseline",
                "chapter": None,
            }
        ]


def test_snapshot_rollback_restores_state() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        state = CanonicalState.create_empty("mybook", "fantasy")
        state.data["world"]["entities"].append(
            {
                "id": "entity-1",
                "name": "Ada",
                "type": "character",
                "attributes": {"role": "lead"},
                "visibility": "active",
            }
        )
        state.save(Path.cwd())

        create_result = runner.invoke(
            cli, ["snapshot", "create", "--json"], catch_exceptions=False
        )
        snapshot_id = json.loads(create_result.output)["snapshot"]["id"]

        current_state = CanonicalState.load(Path.cwd())
        current_state.data["world"]["entities"][0]["name"] = "Bea"
        current_state.save(Path.cwd())

        rollback_result = runner.invoke(
            cli,
            ["snapshot", "rollback", snapshot_id, "--json"],
            catch_exceptions=False,
        )
        show_result = runner.invoke(
            cli, ["state", "show", "--json"], catch_exceptions=False
        )

        assert rollback_result.exit_code == 0
        assert show_result.exit_code == 0
        payload = json.loads(show_result.output)
        assert payload["state"]["world"]["entities"][0]["name"] == "Ada"


def test_snapshot_and_state_diff_json() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        state = CanonicalState.create_empty("mybook", "thriller")
        state.data["world"]["entities"].append(
            {
                "id": "entity-1",
                "name": "Ada",
                "type": "character",
                "attributes": {"role": "lead"},
                "visibility": "active",
            }
        )
        state.save(Path.cwd())
        manager = SnapshotManager(Path.cwd())
        first_id = manager.create_snapshot(state, label="first")

        updated = CanonicalState.load(Path.cwd())
        updated.data["world"]["entities"][0]["name"] = "Ada Quinn"
        updated.data["chapters"].append(
            {
                "number": 1,
                "title": "Opening",
                "status": "draft",
                "summary": "Ada enters the archive.",
                "settled_at": "",
            }
        )
        updated.save(Path.cwd())
        second_id = manager.create_snapshot(updated, label="second")

        snapshot_diff_result = runner.invoke(
            cli,
            ["snapshot", "diff", first_id, second_id, "--json"],
            catch_exceptions=False,
        )
        state_diff_result = runner.invoke(
            cli,
            ["state", "diff", "--snapshot", first_id, "--json"],
            catch_exceptions=False,
        )

        assert snapshot_diff_result.exit_code == 0
        assert state_diff_result.exit_code == 0
        snapshot_payload = json.loads(snapshot_diff_result.output)
        state_payload = json.loads(state_diff_result.output)
        assert snapshot_payload["diff"] == state_payload["diff"]
        assert state_payload["snapshot"]["id"] == first_id
        assert state_payload["diff"]["entities"]["changed"][0]["id"] == "entity-1"
        assert state_payload["diff"]["chapters"]["added"][0]["number"] == 1


def test_snapshot_list_plain_output_empty() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        CanonicalState.create_empty("mybook", "fantasy").save(Path.cwd())

        result = runner.invoke(cli, ["snapshot", "list"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "No snapshots found" in result.output
