from __future__ import annotations

import os
import shlex
import sys
from collections.abc import Callable

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.output.win32 import NoConsoleScreenBufferError


REPL_EXIT_COMMANDS = {"exit", "quit"}
REPL_PROMPT = "novel> "


def run_repl(root_command: click.Command) -> int:
    session = create_repl_session(root_command)
    return repl_loop(
        session=session,
        command_runner=lambda command: dispatch_repl_command(command, root_command),
    )


def repl_loop(
    session: PromptSession,
    command_runner: Callable[[str], int],
) -> int:
    while True:
        try:
            raw_command = session.prompt(REPL_PROMPT)
        except EOFError:
            click.echo()
            return 0
        except KeyboardInterrupt:
            click.echo()
            continue

        command = raw_command.strip()
        if not command:
            continue
        if command in REPL_EXIT_COMMANDS:
            return 0
        command_runner(command)


def dispatch_repl_command(command: str, root_command: click.Command) -> int:
    try:
        root_command.main(
            args=shlex.split(command), prog_name="novel", standalone_mode=False
        )
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 1
    return 0


def build_repl_completer(root_command: click.Command) -> NestedCompleter:
    return NestedCompleter.from_nested_dict(_command_tree(root_command))


def create_repl_session(root_command: click.Command) -> PromptSession:
    return PromptSession(
        completer=build_repl_completer(root_command),
        output=_create_repl_output(),
    )


def _create_repl_output() -> object:
    try:
        return create_output()
    except NoConsoleScreenBufferError:
        return Vt100_Output.from_pty(
            sys.stdout,
            term=os.environ.get("TERM") or "xterm-256color",
        )


def _command_tree(command: click.Command) -> dict[str, dict | None]:
    if not isinstance(command, click.Group):
        return {}

    tree: dict[str, dict | None] = {}
    ctx = click.Context(command)
    for name in command.list_commands(ctx):
        subcommand = command.get_command(ctx, name)
        if subcommand is None:
            continue
        subtree = _command_tree(subcommand)
        tree[name] = subtree or None
    return tree


__all__ = [
    "REPL_EXIT_COMMANDS",
    "REPL_PROMPT",
    "build_repl_completer",
    "create_repl_session",
    "dispatch_repl_command",
    "repl_loop",
    "run_repl",
]
