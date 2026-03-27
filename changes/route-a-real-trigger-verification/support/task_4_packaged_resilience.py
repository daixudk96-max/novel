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
BASE_ENV = {
    "PYTHONPATH": PYTHONPATH_VALUE,
    "NOVEL_LLM_PROVIDER": "openai",
    "NOVEL_LLM_MODEL": "gpt-4o-mini",
    "NOVEL_LLM_API_KEY": "test-key",
    "NOVEL_REAL_VERIFY_FAKE_PROVIDER": "1",
}


def main() -> int:
    recovery = run_recovery_case()
    exhaustion = run_exhaustion_case()
    write_text(EVIDENCE_ROOT / "task-4-packaged-resilience-recovery.txt", recovery)
    write_text(EVIDENCE_ROOT / "task-4-packaged-resilience-exhaustion.txt", exhaustion)
    return 0


def run_recovery_case() -> str:
    workspace = prepare_workspace("retry-recovery")
    seed_commands = seed_workspace(workspace)

    draft_fixture = workspace / "fake-draft-recovery.txt"
    draft_fixture.write_text("Provider-backed recovery draft body.\n", encoding="utf-8")
    call_log_path = workspace / "provider-call-recovery.json"
    env = dict(BASE_ENV)
    env["NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE"] = str(draft_fixture)
    env["NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG"] = str(call_log_path)
    env["NOVEL_REAL_VERIFY_RETRY_SEQUENCE"] = "APIConnectionError,success"

    command = run_command(workspace, env, "chapter", "draft", "--chapter", "1")
    chapter_path = workspace / "mybook" / "chapters" / "chapter_1.md"
    state_path = workspace / "mybook" / "canonical_state.json"
    call_log = read_json_dict(call_log_path)
    state = read_json_dict(state_path)
    chapter_text = (
        chapter_path.read_text(encoding="utf-8") if chapter_path.exists() else ""
    )
    expected_stdout = f"Drafted chapter 1 at {chapter_path}\n"
    expected_chapter = {
        "number": 1,
        "title": "Chapter 1",
        "status": "draft",
        "summary": "Mira takes the next step.",
        "settled_at": "",
    }

    assertions = [
        check(
            command.exit_code == 0, f"exit_code actual={command.exit_code} expected=0"
        ),
        check(
            command.stdout == expected_stdout,
            f"stdout actual={command.stdout!r} expected={expected_stdout!r}",
        ),
        check(command.stderr == "", f"stderr actual={command.stderr!r} expected=''"),
        check(chapter_path.exists(), f"chapter_exists path={chapter_path}"),
        check(
            chapter_text == "Provider-backed recovery draft body.\n",
            f"chapter_text actual={chapter_text!r}",
        ),
        check(
            state.get("chapters") == [expected_chapter],
            f"state_chapters actual={state.get('chapters')!r}",
        ),
        check(
            call_log.get("attempt_count") == 2,
            f"attempt_count actual={call_log.get('attempt_count')!r} expected=2",
        ),
        check(
            call_log.get("prompt")
            == "Draft Chapter 1 about Mira. Summary: Mira takes the next step.",
            f"provider_prompt actual={call_log.get('prompt')!r}",
        ),
        check(
            call_log.get("temperature") == 1.0,
            f"provider_temperature actual={call_log.get('temperature')!r} expected=1.0",
        ),
        check(
            call_log.get("attempts")
            == [
                {
                    "attempt": 1,
                    "outcome": "APIConnectionError",
                    "raised": "APIConnectionError",
                    "message": "simulated APIConnectionError on attempt 1",
                },
                {
                    "attempt": 2,
                    "outcome": "success",
                    "result": "success",
                },
            ],
            f"provider_attempts actual={call_log.get('attempts')!r}",
        ),
    ]

    return render_report(
        title="Task 4 packaged resilience recovery",
        workspace=workspace,
        extra_environment=env,
        commands=[*seed_commands, command],
        sections={
            "Files": {
                "chapter_path": str(chapter_path),
                "chapter_contents": chapter_text,
                "canonical_state_path": str(state_path),
                "canonical_state_json": state,
                "provider_call_log_path": str(call_log_path),
                "provider_call_log_json": call_log,
            },
            "Assertions": assertions,
        },
    )


def run_exhaustion_case() -> str:
    workspace = prepare_workspace("retry-exhaustion")
    seed_commands = seed_workspace(workspace)

    draft_fixture = workspace / "fake-draft-exhaustion.txt"
    draft_fixture.write_text(
        "Provider-backed exhaustion draft body.\n", encoding="utf-8"
    )
    plain_call_log_path = workspace / "provider-call-exhaustion-plain.json"
    json_call_log_path = workspace / "provider-call-exhaustion-json.json"
    retry_sequence = "APIConnectionError,RateLimitError,InternalServerError"

    plain_env = dict(BASE_ENV)
    plain_env["NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE"] = str(draft_fixture)
    plain_env["NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG"] = str(plain_call_log_path)
    plain_env["NOVEL_REAL_VERIFY_RETRY_SEQUENCE"] = retry_sequence

    json_env = dict(plain_env)
    json_env["NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG"] = str(json_call_log_path)

    plain_command = run_command(
        workspace, plain_env, "chapter", "draft", "--chapter", "1"
    )
    json_command = run_command(
        workspace, json_env, "--json", "chapter", "draft", "--chapter", "1"
    )
    chapter_path = workspace / "mybook" / "chapters" / "chapter_1.md"
    state_path = workspace / "mybook" / "canonical_state.json"
    state = read_json_dict(state_path)
    plain_call_log = read_json_dict(plain_call_log_path)
    json_call_log = read_json_dict(json_call_log_path)
    json_payload = json.loads(json_command.stdout)
    expected_error = "chapter draft failed after 3 attempts: simulated InternalServerError on attempt 3"

    assertions = [
        check(
            plain_command.exit_code == 1,
            f"plain_exit_code actual={plain_command.exit_code} expected=1",
        ),
        check(
            plain_command.stdout == "",
            f"plain_stdout actual={plain_command.stdout!r} expected=''",
        ),
        check(
            plain_command.stderr == f"Error: {expected_error}\n",
            f"plain_stderr actual={plain_command.stderr!r}",
        ),
        check(
            json_command.exit_code == 1,
            f"json_exit_code actual={json_command.exit_code} expected=1",
        ),
        check(
            json_payload == {"code": 1, "error": expected_error},
            f"json_payload actual={json_payload!r}",
        ),
        check(
            json_command.stderr == "",
            f"json_stderr actual={json_command.stderr!r} expected=''",
        ),
        check(not chapter_path.exists(), f"chapter_absent path={chapter_path}"),
        check(
            state.get("chapters") == [],
            f"state_chapters actual={state.get('chapters')!r} expected=[]",
        ),
        check(
            plain_call_log.get("attempt_count") == 3,
            f"plain_attempt_count actual={plain_call_log.get('attempt_count')!r} expected=3",
        ),
        check(
            json_call_log.get("attempt_count") == 3,
            f"json_attempt_count actual={json_call_log.get('attempt_count')!r} expected=3",
        ),
        check(
            plain_call_log.get("attempts")
            == [
                {
                    "attempt": 1,
                    "outcome": "APIConnectionError",
                    "raised": "APIConnectionError",
                    "message": "simulated APIConnectionError on attempt 1",
                },
                {
                    "attempt": 2,
                    "outcome": "RateLimitError",
                    "raised": "RateLimitError",
                    "message": "simulated RateLimitError on attempt 2",
                },
                {
                    "attempt": 3,
                    "outcome": "InternalServerError",
                    "raised": "InternalServerError",
                    "message": "simulated InternalServerError on attempt 3",
                },
            ],
            f"plain_provider_attempts actual={plain_call_log.get('attempts')!r}",
        ),
        check(
            json_call_log.get("attempts")
            == [
                {
                    "attempt": 1,
                    "outcome": "APIConnectionError",
                    "raised": "APIConnectionError",
                    "message": "simulated APIConnectionError on attempt 1",
                },
                {
                    "attempt": 2,
                    "outcome": "RateLimitError",
                    "raised": "RateLimitError",
                    "message": "simulated RateLimitError on attempt 2",
                },
                {
                    "attempt": 3,
                    "outcome": "InternalServerError",
                    "raised": "InternalServerError",
                    "message": "simulated InternalServerError on attempt 3",
                },
            ],
            f"json_provider_attempts actual={json_call_log.get('attempts')!r}",
        ),
    ]

    return render_report(
        title="Task 4 packaged resilience exhaustion",
        workspace=workspace,
        extra_environment=plain_env,
        commands=[*seed_commands, plain_command, json_command],
        sections={
            "Files": {
                "chapter_path": str(chapter_path),
                "chapter_exists": chapter_path.exists(),
                "canonical_state_path": str(state_path),
                "canonical_state_json": state,
                "plain_provider_call_log_path": str(plain_call_log_path),
                "plain_provider_call_log_json": plain_call_log,
                "json_provider_call_log_path": str(json_call_log_path),
                "json_provider_call_log_json": json_call_log,
            },
            "Assertions": assertions,
        },
    )


def seed_workspace(workspace: Path) -> list[CommandResult]:
    env = {"PYTHONPATH": PYTHONPATH_VALUE}
    init_result = run_command(
        workspace, env, "project", "init", "mybook", "--genre", "fantasy"
    )
    require(
        init_result.exit_code == 0,
        f"project init failed: {init_result.stderr or init_result.stdout}",
    )
    entity_result = run_command(
        workspace,
        env,
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
    require(
        entity_result.exit_code == 0,
        f"world entity add failed: {entity_result.stderr or entity_result.stdout}",
    )
    return [init_result, entity_result]


def prepare_workspace(name: str) -> Path:
    workspace = RUNTIME_ROOT / name
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def run_command(
    cwd: Path,
    env_updates: dict[str, str],
    *args: str,
) -> CommandResult:
    env = dict(env_updates)
    full_env = dict(os.environ)
    full_env.update(env)
    start = time.perf_counter()
    completed = subprocess.run(
        [str(NOVEL_EXE), *args],
        cwd=cwd,
        env=full_env,
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    result = CommandResult(
        argv=(str(NOVEL_EXE), *args),
        cwd=cwd,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        elapsed_seconds=round(elapsed, 3),
    )
    return result


def render_report(
    *,
    title: str,
    workspace: Path,
    extra_environment: dict[str, str],
    commands: list[CommandResult],
    sections: dict[str, object],
) -> str:
    lines = [
        title,
        "",
        f"Workspace: {workspace}",
        f"Packaged entrypoint: {NOVEL_EXE}",
        "",
        "Environment",
        f"  PYTHONPATH={PYTHONPATH_VALUE}",
    ]
    for key, value in extra_environment.items():
        if key == "PYTHONPATH":
            continue
        lines.append(f"  {key}={value}")
    lines.extend(["", "Commands"])
    for index, command in enumerate(commands, start=1):
        lines.extend(render_command(index, command))
    for heading, payload in sections.items():
        lines.extend(["", heading])
        if isinstance(payload, list):
            for item in payload:
                lines.append(f"  - {item}")
            continue
        if isinstance(payload, dict):
            for key, value in payload.items():
                rendered = (
                    json.dumps(value, indent=2)
                    if isinstance(value, (dict, list))
                    else str(value)
                )
                lines.append(f"  {key}: {rendered}")
            continue
        lines.append(f"  {payload}")
    assertion_lines = sections.get("Assertions", [])
    if not isinstance(assertion_lines, list):
        raise RuntimeError("Assertions section must be a list")
    overall = (
        "PASS"
        if all(
            isinstance(item, str) and item.startswith("PASS")
            for item in assertion_lines
        )
        else "FAIL"
    )
    lines.extend(["", f"Overall: {overall}"])
    return "\n".join(lines) + "\n"


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


if __name__ == "__main__":
    raise SystemExit(main())
