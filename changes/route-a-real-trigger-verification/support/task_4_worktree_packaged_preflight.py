from __future__ import annotations

import json
import os
import shutil
import subprocess
import sysconfig
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: Path
    exit_code: int
    stdout: str
    stderr: str
    elapsed_seconds: float


ROOT = Path(__file__).resolve().parents[3]
CHANGE_ROOT = ROOT / "changes" / "route-a-real-trigger-verification"
RUNTIME_ROOT = CHANGE_ROOT / "runtime"
EVIDENCE_ROOT = CHANGE_ROOT / "evidence"
SUPPORT_ROOT = CHANGE_ROOT / "support"
WORKTREE_RUNTIME = ROOT / "novel-runtime"
WORKTREE_CLI = ROOT / "novel-cli"
NOVEL_EXE = Path(sysconfig.get_path("scripts")) / "novel.exe"
PYTHONPATH_VALUE = ";".join(
    [
        str(SUPPORT_ROOT),
        str(WORKTREE_CLI),
        str(WORKTREE_RUNTIME),
    ]
)


def main() -> int:
    report = run_worktree_preflight()
    write_text(EVIDENCE_ROOT / "task-4-packaged-worktree-preflight.txt", report)
    return 0


def run_worktree_preflight() -> str:
    workspace = RUNTIME_ROOT / "worktree-preflight"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    base_env = {"PYTHONPATH": PYTHONPATH_VALUE}
    help_result = run_command(workspace, base_env, "--help")
    init_result = run_command(
        workspace, base_env, "project", "init", "mybook", "--genre", "fantasy"
    )
    entity_result = run_command(
        workspace,
        base_env,
        "world",
        "entity",
        "add",
        "--name",
        "Mira",
        "--type",
        "character",
        "--attributes",
        '{"role": "lead"}',
    )

    plain_result = run_command(
        workspace, base_env, "chapter", "draft", "--chapter", "1"
    )
    json_result = run_command(
        workspace, base_env, "--json", "chapter", "draft", "--chapter", "1"
    )

    state_path = workspace / "mybook" / "canonical_state.json"
    chapter_path = workspace / "mybook" / "chapters" / "chapter_1.md"
    state = read_json_dict(state_path)
    json_payload = json.loads(json_result.stdout)
    expected_error = "NOVEL_LLM_PROVIDER is required for Route A provider resolution"

    assertions = [
        check(
            help_result.exit_code == 0,
            f"help_exit_code actual={help_result.exit_code} expected=0",
        ),
        check(
            "chapter" in help_result.stdout,
            "help_contains_chapter actual=True expected=True",
        ),
        check(
            init_result.exit_code == 0,
            f"init_exit_code actual={init_result.exit_code} expected=0",
        ),
        check(
            entity_result.exit_code == 0,
            f"entity_exit_code actual={entity_result.exit_code} expected=0",
        ),
        check(
            plain_result.exit_code == 1,
            f"plain_exit_code actual={plain_result.exit_code} expected=1",
        ),
        check(
            plain_result.stdout == "",
            f"plain_stdout actual={plain_result.stdout!r} expected=''",
        ),
        check(
            plain_result.stderr == f"Error: {expected_error}\n",
            f"plain_stderr actual={plain_result.stderr!r}",
        ),
        check(
            json_result.exit_code == 1,
            f"json_exit_code actual={json_result.exit_code} expected=1",
        ),
        check(
            json_payload == {"code": 1, "error": expected_error},
            f"json_payload actual={json_payload!r}",
        ),
        check(
            json_result.stderr == "",
            f"json_stderr actual={json_result.stderr!r} expected=''",
        ),
        check(not chapter_path.exists(), f"chapter_absent path={chapter_path}"),
        check(
            state.get("chapters") == [],
            f"state_chapters actual={state.get('chapters')!r} expected=[]",
        ),
    ]

    lines = [
        "Task 4 packaged worktree preflight",
        "",
        f"Workspace: {workspace}",
        f"Packaged entrypoint: {NOVEL_EXE}",
        "",
        "Environment",
        f"  PYTHONPATH={PYTHONPATH_VALUE}",
        "  NOVEL_REAL_VERIFY_FAKE_PROVIDER=<unset>",
        "  NOVEL_LLM_PROVIDER=<unset>",
        "  NOVEL_LLM_MODEL=<unset>",
        "  NOVEL_LLM_API_KEY=<unset>",
        "",
        "Commands",
        *render_command(1, help_result),
        *render_command(2, init_result),
        *render_command(3, entity_result),
        *render_command(4, plain_result),
        *render_command(5, json_result),
        "",
        "Files",
        f"  canonical_state_path: {state_path}",
        f"  canonical_state_json: {json.dumps(state, indent=2)}",
        f"  chapter_path: {chapter_path}",
        f"  chapter_exists: {chapter_path.exists()}",
        "",
        "Assertions",
    ]
    lines.extend(f"  - {item}" for item in assertions)
    overall = "PASS" if all(item.startswith("PASS") for item in assertions) else "FAIL"
    lines.extend(["", f"Overall: {overall}"])
    return "\n".join(lines) + "\n"


def run_command(cwd: Path, env_updates: dict[str, str], *args: str) -> CommandResult:
    env = dict(os.environ)
    env.update(env_updates)
    start = time.perf_counter()
    completed = subprocess.run(
        [str(NOVEL_EXE), *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    return CommandResult(
        argv=(str(NOVEL_EXE), *args),
        cwd=cwd,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        elapsed_seconds=round(elapsed, 3),
    )


def render_command(index: int, command: CommandResult) -> list[str]:
    return [
        f"  {index}. cwd: {command.cwd}",
        f"     argv: {' '.join(command.argv)}",
        f"     exit_code: {command.exit_code}",
        f"     elapsed_seconds: {command.elapsed_seconds}",
        f"     stdout: {command.stdout!r}",
        f"     stderr: {command.stderr!r}",
    ]


def read_json_dict(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object in {path}")
    return data


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def check(condition: bool, detail: str) -> str:
    return f"{'PASS' if condition else 'FAIL'} | {detail}"


if __name__ == "__main__":
    raise SystemExit(main())
