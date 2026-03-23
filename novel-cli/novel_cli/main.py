from __future__ import annotations

import sys

import click

from novel_cli import __version__
from novel_cli.commands import project_group
from novel_cli.commands.chapter import chapter_group
from novel_cli.commands.snapshot import snapshot_group
from novel_cli.commands.state import state_group
from novel_cli.commands.world import world_group
from novel_cli.output import OutputFormatter
from novel_cli.repl import run_repl


class NovelGroup(click.Group):
    def main(
        self,
        args=None,
        prog_name=None,
        complete_var=None,
        standalone_mode=True,
        **extra,
    ):
        formatter = OutputFormatter()
        raw_args = _coerce_args(args)
        global_json = _has_global_json_flag(raw_args)
        actual_args = _inject_command_json_flag(raw_args) if global_json else raw_args

        try:
            return super().main(
                args=actual_args,
                prog_name=prog_name,
                complete_var=complete_var,
                standalone_mode=False,
                **extra,
            )
        except click.ClickException as exc:
            if global_json:
                click.echo(
                    formatter.error_format(
                        {"error": exc.format_message(), "code": exc.exit_code},
                        mode="json",
                    )
                )
            else:
                exc.show()
            raise SystemExit(exc.exit_code) from exc
        except click.exceptions.Exit:
            raise
        except Exception as exc:
            if not global_json:
                raise
            click.echo(formatter.error_format(exc, mode="json"))
            raise SystemExit(1) from exc


def _coerce_args(args: list[str] | tuple[str, ...] | None) -> list[str]:
    if args is None:
        return sys.argv[1:]
    return list(args)


def _has_global_json_flag(args: list[str] | tuple[str, ...] | None) -> bool:
    return bool(args) and "--json" in args


def _inject_command_json_flag(
    args: list[str] | tuple[str, ...] | None,
) -> list[str] | tuple[str, ...] | None:
    if not args:
        return args
    normalized = [arg for arg in args if arg != "--json"]
    if normalized and "--json" not in normalized:
        normalized.append("--json")
    return normalized


@click.group(name="novel", cls=NovelGroup)
@click.version_option(version=__version__, prog_name="novel")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
@click.pass_context
def cli(ctx: click.Context, json_output: bool) -> None:
    ctx.ensure_object(dict)
    ctx.obj["output_mode"] = "json" if json_output else "plain"


@cli.command("repl")
def repl_command() -> None:
    run_repl(cli)


cli.add_command(project_group)
cli.add_command(chapter_group)
cli.add_command(world_group)
cli.add_command(state_group)
cli.add_command(snapshot_group)
