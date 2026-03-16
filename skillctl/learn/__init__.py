"""skillctl learn — interactive guide to writing agent skills."""

from typing import Annotated, Optional

import typer

from ..output import print_error, print_json

learn_app = typer.Typer(
    name="learn",
    help="Learn how to write, organize, and maintain agent skills.",
    no_args_is_help=False,
)


@learn_app.callback(invoke_without_command=True)
def learn_callback(
    ctx: typer.Context,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Learn how to build great agent skills."""
    if ctx.invoked_subcommand is not None:
        return
    from .renderer import render_index

    result = render_index(json_output=json_output)
    if result:
        print_json(result)


@learn_app.command()
def anatomy(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """What makes a great skill — the five layers."""
    from .renderer import render_anatomy

    result = render_anatomy(json_output=json_output)
    if result:
        print_json(result)


@learn_app.command()
def write(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Writing for AI comprehension — do's and don'ts."""
    from .renderer import render_write

    result = render_write(json_output=json_output)
    if result:
        print_json(result)


@learn_app.command()
def organize(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Structuring your skills library."""
    from .renderer import render_organize

    result = render_organize(json_output=json_output)
    if result:
        print_json(result)


@learn_app.command()
def examples(
    name: Annotated[
        Optional[str],
        typer.Argument(help="Example skill name"),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Browse well-written example skills."""
    from .renderer import render_examples

    result = render_examples(name=name, json_output=json_output)
    if result:
        if result.get("status") == "error":
            print_error(result["message"], json_output=json_output, code=2)
            raise typer.Exit(2)
        print_json(result)
