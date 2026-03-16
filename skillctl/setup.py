"""First-run setup — triggered once when no config exists.

Shows sensible defaults, lets user accept with Enter.
Skipped automatically in non-interactive contexts (--json, --quiet, pipes).
"""

import os
import sys

import typer

from .config import (
    CONFIG_PATH,
    DEFAULT_SKILLS_DIR,
    SKILLCTL_DIR,
    Config,
    _detect_gh_token,
    save_config,
)


def needs_setup() -> bool:
    """Check if first-run setup should trigger."""
    if CONFIG_PATH.exists():
        return False
    if os.environ.get("SKILLCTL_SKIP_SETUP"):
        return False
    if not sys.stdin.isatty():
        return False
    return True


def run_setup() -> None:
    """Run the interactive first-run setup."""
    from rich.text import Text

    from .output import console, print_success
    from .theme import get_logo_lines

    console.print()

    # ── Logo ──
    for skill_part, ctl_part in get_logo_lines():
        line = Text("  ")
        line.append(skill_part, style="bold")
        line.append(" ")
        line.append(ctl_part, style="bold green")
        console.print(line)

    console.print()
    console.print("  [bold]Welcome to skillctl![/]")
    console.print(
        "  [dim]Let's get you set up. Press Enter to accept defaults.[/]"
    )

    # ── 1. Skills directory ──
    console.print()
    console.print("  [bold blue]1.[/] [bold]Skills directory[/]")
    console.print("  [dim]Where do your agent skills live?[/]")
    skills_dir = typer.prompt(
        "  ",
        default=str(DEFAULT_SKILLS_DIR),
        show_default=True,
    ).strip()
    if not skills_dir:
        skills_dir = str(DEFAULT_SKILLS_DIR)

    # ── 2. LLM enrichment ──
    console.print()
    console.print(
        "  [bold blue]2.[/] [bold]Search enrichment[/] [dim](optional)[/]"
    )
    console.print()
    console.print(
        "  [dim]skillctl can use an LLM to generate search keywords for skills,[/]"
    )
    console.print(
        '  [dim]making search much better (e.g. "excel" finds the xlsx skill).[/]'
    )
    console.print()
    console.print(
        "  [dim]How it works:[/]"
    )
    console.print(
        "  [dim]  • Runs once when building the search index[/]"
    )
    console.print(
        "  [dim]  • ~$0.0005 per skill with Haiku, ~$0.001 with GPT-5 mini[/]"
    )
    console.print(
        "  [dim]  • Results are cached — subsequent searches are free[/]"
    )
    console.print(
        "  [dim]  • Keys stay local in ~/.skillctl/config.yaml[/]"
    )
    console.print(
        "  [dim]  • Calls go directly from your machine to the API — no intermediary[/]"
    )
    console.print()

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    has_any_key = bool(anthropic_key or openai_key)

    if anthropic_key:
        console.print(
            f"  [green]●[/] Anthropic key [green]detected[/]"
            f" [dim]({anthropic_key[:12]}...)[/]"
        )
    if openai_key:
        console.print(
            f"  [green]●[/] OpenAI key [green]detected[/]"
            f" [dim]({openai_key[:12]}...)[/]"
        )

    if has_any_key:
        console.print()
        console.print(
            "  [dim]Enrichment will use your detected key(s) automatically.[/]"
        )
        console.print(
            "  [dim]To disable: skillctl config set enrichment off[/]"
        )
    else:
        console.print("  [dim]○[/] No API keys detected")
        console.print()

        key_input = typer.prompt(
            "    ANTHROPIC_API_KEY (or Enter to skip)",
            default="",
            show_default=False,
        ).strip()
        if key_input:
            anthropic_key = key_input
        else:
            key_input = typer.prompt(
                "    OPENAI_API_KEY (or Enter to skip)",
                default="",
                show_default=False,
            ).strip()
            if key_input:
                openai_key = key_input

        if not anthropic_key and not openai_key:
            console.print()
            console.print(
                "  [dim]No problem — search still works, just without[/]"
            )
            console.print(
                "  [dim]enriched keywords. Add a key anytime:[/]"
            )
            console.print(
                "  [dim]  export ANTHROPIC_API_KEY=sk-...[/]"
            )

    # ── 3. GitHub auth ──
    console.print()
    console.print("  [bold blue]3.[/] [bold]GitHub[/]")

    gh_token = _detect_gh_token()
    if gh_token:
        console.print(
            "  [green]●[/] Authenticated [green]via gh CLI[/]"
        )
    else:
        console.print(
            "  [dim]○[/] Not authenticated"
            " [dim](install gh CLI for higher API rate limits)[/]"
        )

    # ── Save ──
    SKILLCTL_DIR.mkdir(parents=True, exist_ok=True)
    config = Config(skills_dir=skills_dir)
    config.github_token = gh_token
    save_config(config)

    console.print()
    print_success(f"Saved to [yellow]{CONFIG_PATH}[/]")
    console.print()
