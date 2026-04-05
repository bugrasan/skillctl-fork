"""skillctl CLI — package manager for agent skills."""

import re
from pathlib import Path
from typing import Annotated, Optional

import typer

from . import __version__, manifest
from .config import (
    CONFIG_PATH,
    VALID_KEYS,
    load_config,
    set_config_value,
)
from .output import (
    console,
    err_console,
    filter_fields,
    print_dim,
    print_error,
    print_info,
    print_json,
    print_success,
    print_warning,
)

REPO_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")
REPO_PATTERN_STR = r"^[\w.-]+/[\w.-]+$"
SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
SLUG_PATTERN_STR = r"^[a-zA-Z0-9_-]+$"

app = typer.Typer(
    name="skillctl",
    help="Package manager for agent skills.",
    no_args_is_help=False,
    add_completion=True,
    rich_markup_mode="rich",
)

# ── Subcommand groups ──

from .learn import learn_app  # noqa: E402

app.add_typer(learn_app, name="learn")


# ── Helpers ──


def _repo_slug(repo: str) -> str:
    """Convert 'user/repo' to filesystem-safe 'user__repo'."""
    return repo.replace("/", "__")


def _installed_names(complete: str = "") -> list[str]:
    """Completion callback: installed skill names."""
    return [s["slug"] for s in manifest.list_skills()]


def _git_installed_names(complete: str = "") -> list[str]:
    """Completion callback: git-installed skill names."""
    return [
        s["slug"]
        for s in manifest.list_skills()
        if s.get("source") == "github"
    ]


def _skills_sharing_clone(clone_path: str, exclude_slug: str) -> list[str]:
    """Find other skills that share the same clone_path."""
    return [
        s["slug"]
        for s in manifest.list_skills()
        if s.get("clone_path") == clone_path
        and s.get("slug") != exclude_slug
    ]


# ── Root callback ──


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool, typer.Option("--version", "-v", help="Show version")
    ] = False,
):
    """skillctl — package manager for agent skills."""
    if version:
        print(f"skillctl {__version__}")
        raise typer.Exit()

    # First-run setup — only when interactive and no config exists
    from .setup import needs_setup, run_setup

    if needs_setup():
        run_setup()

    if ctx.invoked_subcommand is None:
        _show_welcome()


def _show_welcome():
    from rich.align import Align
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    from .animation import play_boot_animation
    from .theme import get_logo_lines

    W = 58  # fixed content width — all blocks pad to this

    def _pad(t: Text) -> Text:
        gap = W - len(t.plain)
        if gap > 0:
            t.append(" " * gap)
        return t

    # ── Animated logo ──
    animated = play_boot_animation(console)

    if not animated:
        console.print()
        for skill_part, ctl_part in get_logo_lines():
            line = Text()
            line.append(skill_part, style="bold")
            line.append(" ")
            line.append(ctl_part, style="bold green")
            console.print(Align.center(_pad(line)))

    console.print()

    # ── Hero copy — two lines, from your landing page ──
    h1 = Text()
    h1.append("The package manager for agent skills.", style="bold")
    console.print(Align.center(h1))
    h2 = Text()
    h2.append(
        "Search, install, and manage SKILL.md files.",
        style="dim",
    )
    console.print(Align.center(h2))
    h3 = Text()
    h3.append("Stateless, zero-config, and token-efficient.", style="dim")
    console.print(Align.center(h3))
    console.print()

    # ── Quick-start panel ──
    qs = Text()
    qs.append("$ ", style="green")
    qs.append("pip install skillctl\n")
    qs.append("$ ", style="green")
    qs.append('skillctl search "pdf"\n')
    qs.append("$ ", style="green")
    qs.append("skillctl install anthropics/skills")
    console.print(
        Align.center(
            Panel(
                qs,
                box=box.ROUNDED,
                border_style="dim green",
                width=48,
                padding=(0, 2),
            )
        )
    )
    console.print()

    # ── Feature pillars — three numbers like the landing page ──
    nums = [
        ("0", "tokens when idle", "No server, no protocol"),
        ("1", "command to install", "Clone, symlink, done"),
        ("\u221e", "LLM-compatible", "Agents already know CLI"),
    ]
    COL = 20

    num_line = Text()
    lbl_line = Text()
    sub_line = Text()
    for i, (n, label, sub) in enumerate(nums):
        if i > 0:
            num_line.append("  ")
            lbl_line.append("  ")
            sub_line.append("  ")
        num_line.append(f"{n:<{COL}}", style="bold green")
        lbl_line.append(f"{label:<{COL}}", style="bold")
        sub_line.append(f"{sub:<{COL}}", style="dim")
    console.print(Align.center(num_line))
    console.print(Align.center(lbl_line))
    console.print(Align.center(sub_line))
    console.print()

    # ── Command grid ──
    commands = [
        ("search",  "Find skills",     "create",  "Scaffold a skill"),
        ("install", "From GitHub",      "update",  "Pull latest"),
        ("list",    "Installed skills", "remove",  "Uninstall"),
        ("info",    "Skill details",    "config",  "Configuration"),
        ("learn",   "Best practices",   "lint",    "Score & validate"),
    ]

    grid_lines: list[Text] = []
    for left_cmd, left_desc, right_cmd, right_desc in commands:
        ls = "bold green" if left_cmd in ("learn", "lint") else "bold"
        rs = "bold green" if right_cmd in ("learn", "lint") else "bold"

        line = Text()
        line.append(f"{left_cmd:<9}", style=ls)
        line.append(f"{left_desc:<19}", style="")
        line.append(f"{right_cmd:<9}", style=rs)
        line.append(right_desc, style="")
        grid_lines.append(_pad(line))

    console.print(Align.center(Text("\n").join(grid_lines)))

    console.print()
    footer = Text()
    footer.append("skillctl <command> --help", style="bold")
    footer.append("  for details", style="dim")
    console.print(Align.center(footer))

    ver = Text()
    ver.append(f"v{__version__}", style="dim")
    console.print(Align.center(ver))
    console.print()


# ══════════════════════════════════════════════
# SCHEMA (P0-1)
# ══════════════════════════════════════════════


@app.command()
def schema(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = True,
):
    """Dump CLI schema for agent self-discovery."""
    schema_data = {
        "name": "skillctl",
        "version": __version__,
        "commands": {
            "search": {
                "description": "Find skills locally and on GitHub",
                "args": {
                    "query": {"type": "string", "required": True},
                },
                "flags": {
                    "--source": {
                        "type": "enum",
                        "values": [
                            "local",
                            "registry",
                            "github",
                            "all",
                        ],
                        "default": "all",
                        "description": "local=filesystem, registry=trusted repos (default remote), github=broad search, all=local+registry",
                    },
                    "--tags": {"type": "string"},
                    "--sort": {
                        "type": "enum",
                        "values": ["stars", "name", "updated"],
                        "default": "stars",
                    },
                    "--limit": {"type": "int", "default": 20},
                    "--offset": {"type": "int", "default": 0},
                    "--json": {"type": "bool"},
                    "--fields": {
                        "type": "string",
                        "description": "Comma-separated field names",
                    },
                },
            },
            "install": {
                "description": "Install a skill from GitHub",
                "args": {
                    "repo": {
                        "type": "string",
                        "required": True,
                        "pattern": REPO_PATTERN_STR,
                    },
                },
                "flags": {
                    "--path": {"type": "string"},
                    "--dry-run": {"type": "bool"},
                    "--json": {"type": "bool"},
                    "--yes": {"type": "bool"},
                    "--quiet": {"type": "bool"},
                },
            },
            "list": {
                "description": "Show all installed skills",
                "args": {},
                "flags": {
                    "--json": {"type": "bool"},
                    "--fields": {"type": "string"},
                    "--quiet": {"type": "bool"},
                },
            },
            "create": {
                "description": "Scaffold a new skill",
                "args": {
                    "slug": {
                        "type": "string",
                        "required": True,
                        "pattern": SLUG_PATTERN_STR,
                    },
                },
                "flags": {
                    "--name": {"type": "string"},
                    "--desc": {"type": "string"},
                    "--tags": {"type": "string"},
                    "--author": {"type": "string"},
                    "--yes": {"type": "bool"},
                    "--json": {"type": "bool"},
                },
            },
            "update": {
                "description": "Pull latest versions for git-installed skills",
                "args": {
                    "name": {"type": "string", "required": False},
                },
                "flags": {
                    "--all": {"type": "bool"},
                    "--json": {"type": "bool"},
                    "--quiet": {"type": "bool"},
                },
            },
            "remove": {
                "description": "Remove an installed skill",
                "args": {
                    "name": {"type": "string", "required": True},
                },
                "flags": {
                    "--yes": {"type": "bool"},
                    "--dry-run": {"type": "bool"},
                    "--json": {"type": "bool"},
                },
            },
            "info": {
                "description": "Show details of a specific skill",
                "args": {
                    "name": {"type": "string", "required": True},
                },
                "flags": {
                    "--json": {"type": "bool"},
                    "--fields": {"type": "string"},
                },
            },
            "config": {
                "description": "View and set configuration",
                "subcommands": {
                    "set": {
                        "args": {
                            "key": {"type": "string", "required": True},
                            "value": {"type": "string", "required": True},
                        },
                    },
                    "get": {
                        "args": {
                            "key": {"type": "string", "required": True},
                        },
                    },
                },
            },
            "schema": {
                "description": "Dump CLI schema for agent self-discovery",
                "args": {},
                "flags": {"--json": {"type": "bool", "default": True}},
            },
            "learn": {
                "description": "Learn how to write, organize, and maintain skills",
                "subcommands": {
                    "anatomy": {
                        "description": "The five layers every great skill needs",
                        "flags": {"--json": {"type": "bool"}},
                    },
                    "write": {
                        "description": "Writing for AI comprehension — do's and don'ts",
                        "flags": {"--json": {"type": "bool"}},
                    },
                    "organize": {
                        "description": "Directory structure, naming, and tagging",
                        "flags": {"--json": {"type": "bool"}},
                    },
                    "examples": {
                        "description": "Browse well-written example skills",
                        "args": {
                            "name": {"type": "string", "required": False},
                        },
                        "flags": {"--json": {"type": "bool"}},
                    },
                },
                "flags": {"--json": {"type": "bool"}},
            },
            "lint": {
                "description": "Score and validate a skill against best practices",
                "args": {
                    "name": {"type": "string", "required": True},
                },
                "flags": {
                    "--json": {"type": "bool"},
                },
            },
            "registry": {
                "description": "Manage trusted skill registries",
                "subcommands": {
                    "list": {"description": "List configured registries"},
                    "add": {
                        "description": "Add a trusted registry (validates skills exist)",
                        "args": {"repo": {"type": "string", "required": True, "pattern": REPO_PATTERN_STR}},
                    },
                    "remove": {
                        "description": "Remove a registry",
                        "args": {"repo": {"type": "string", "required": True}},
                    },
                    "reset": {"description": "Reset to default registries"},
                },
                "flags": {"--json": {"type": "bool"}},
            },
        },
        "exit_codes": {
            "0": "success",
            "1": "runtime error",
            "2": "not found / bad input",
        },
    }
    print_json(schema_data)


# ══════════════════════════════════════════════
# SEARCH (P0-2: --limit/--offset)
# ══════════════════════════════════════════════


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    source: Annotated[
        str,
        typer.Option(
            "--source",
            "-s",
            help="Source: local, registry, github, all",
        ),
    ] = "all",
    tags: Annotated[
        Optional[str],
        typer.Option("--tags", help="Filter by tags (comma-separated)"),
    ] = None,
    sort: Annotated[
        str,
        typer.Option("--sort", help="Sort: stars, name, updated"),
    ] = "stars",
    limit: Annotated[
        int,
        typer.Option("--limit", help="Max results to return"),
    ] = 20,
    offset: Annotated[
        int,
        typer.Option("--offset", help="Skip first N results"),
    ] = 0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    fields: Annotated[
        Optional[str],
        typer.Option("--fields", help="Comma-separated fields (JSON only)"),
    ] = None,
):
    """Find skills locally, in registries, and on GitHub."""
    from .discovery.github import GitHubRateLimitError, search_github
    from .discovery.local import search_local
    from .discovery.ranking import merge_and_rank
    from .discovery.registry import search_registries
    from .renderables import SearchLedger

    config = load_config()
    local_results: list[dict] = []
    remote_results: list[dict] = []

    if source in ("local", "all"):
        local_results = search_local(config, query)
        if not json_output:
            err_console.print(
                f"  [chrome]Searching local skills..."
                f" {len(local_results)} found[/]"
            )

    # Registry search (default remote source)
    if source in ("registry", "all"):
        registry_results = search_registries(config, query)
        if not json_output:
            reg_names = ", ".join(config.registries)
            err_console.print(
                f"  [chrome]Searching registries"
                f" ({reg_names})..."
                f" {len(registry_results)} found[/]"
            )
        remote_results.extend(registry_results)

    # Broad GitHub search (opt-in, noisy)
    if source == "github":
        try:
            github_results = search_github(config, query, sort=sort)
        except GitHubRateLimitError as e:
            if not json_output:
                print_warning(str(e))
            github_results = []
        if not github_results:
            if not json_output:
                print_warning(
                    "GitHub search unavailable."
                )
        elif not json_output:
            err_console.print(
                f"  [chrome]Searching GitHub..."
                f" {len(github_results)} found[/]"
            )
        remote_results.extend(github_results)

    # Filter by tags
    if tags:
        tag_set = {t.strip().lower() for t in tags.split(",")}
        local_results = [
            r
            for r in local_results
            if tag_set & {t.lower() for t in r.get("tags", [])}
        ]
        remote_results = [
            r
            for r in remote_results
            if tag_set & {t.lower() for t in r.get("tags", [])}
        ]

    results = merge_and_rank(local_results, remote_results, sort=sort)
    total = len(results)

    # Apply pagination
    results = results[offset : offset + limit]

    if json_output:
        output = filter_fields(results, fields)
        next_actions = []
        if results:
            top = results[0]
            if not top.get("installed") and top.get("source") in (
                "github",
                "registry",
            ):
                repo = top.get("repo", top.get("name", ""))
                path_in_repo = top.get("path_in_repo", "")
                install_cmd = f"skillctl install {repo}"
                if path_in_repo and path_in_repo != ".":
                    install_cmd += f" --path {path_in_repo}"
                next_actions.append(f"{install_cmd} -y --json")
            next_actions.append(
                f"skillctl info {results[0].get('slug', results[0].get('name', ''))} --json"
            )
        else:
            next_actions.append(
                f'skillctl search "{query}" --source=registry --json'
            )
            slug = query.replace(" ", "-").lower()
            next_actions.append(
                f'skillctl create {slug} --name "{query}" -y --json'
            )
        print_json(output, next_actions=next_actions)
    else:
        if not results:
            console.print(
                f'\n  [dim]No skills found for[/] [yellow]"{query}"[/]'
            )
            console.print(
                f"  [dim]Try:[/] [bold]skillctl search[/]"
                f' [yellow]"{query}"[/] [cyan]--source=github[/]'
            )
            console.print()
            raise typer.Exit(2)

        console.print()
        console.print(SearchLedger(results, total))
        if any(not r.get("installed") for r in results):
            console.print(
                "  [chrome]Install with:[/]"
                " [bold]skillctl install[/] [machine]<name>[/]"
            )
        console.print()


# ══════════════════════════════════════════════
# INSTALL (P1-6: expected_pattern in errors)
# ══════════════════════════════════════════════


@app.command()
def install(
    repo: Annotated[
        str, typer.Argument(help="GitHub repo (user/repo format)")
    ],
    path: Annotated[
        Optional[str],
        typer.Option("--path", help="Subdirectory for monorepos"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without executing"),
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmations")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress progress")
    ] = False,
):
    """Install a skill from GitHub."""
    from .importer.git_ops import clone_repo, is_git_repo, pull_repo
    from .importer.linker import create_symlink, remove_clone, remove_symlink
    from .renderables import DryRunPreview, InstallReceipt

    if not REPO_PATTERN.match(repo):
        print_error(
            f"Invalid repo format: {repo}. Expected: user/repo",
            json_output=json_output,
            code=2,
            expected_pattern=REPO_PATTERN_STR,
        )
        raise typer.Exit(2)

    config = load_config()
    slug = Path(path).name if path else repo.split("/")[1]
    repo_dir_name = _repo_slug(repo)
    clone_path = config.repos_path / repo_dir_name
    skill_source = clone_path / path if path else clone_path
    symlink_target = config.skills_path / slug

    # Already installed — try to update
    existing = manifest.get_skill(slug)
    if existing:
        _handle_reinstall(
            slug, clone_path, existing, json_output, quiet,
            token=config.github_token,
        )
        return

    # Dry-run
    if dry_run:
        _install_dry_run(
            repo, clone_path, skill_source, symlink_target, slug,
            json_output,
        )
        return

    # Clone — clean stale clone dir if it exists but isn't tracked
    if clone_path.exists() and not manifest.get_skill(slug):
        remove_clone(clone_path)

    try:
        clone_path.parent.mkdir(parents=True, exist_ok=True)
        commit = clone_repo(repo, clone_path, token=config.github_token)
        if not json_output and not quiet:
            print_success(
                f"Cloned [blue]{repo}[/] → [dim]{clone_path}[/]"
            )
    except RuntimeError as e:
        print_error(str(e), json_output=json_output, code=2)
        raise typer.Exit(2)
    except PermissionError:
        print_error(
            f"Cannot clone to {clone_path}",
            json_output=json_output,
            code=1,
            hint=f"Permission denied on {config.repos_path}",
        )
        raise typer.Exit(1)

    # Verify skill source path exists
    if not skill_source.exists():
        msg = (
            f"Path not found in repo: {path}"
            if path
            else "Clone succeeded but directory is empty"
        )
        print_error(msg, json_output=json_output, code=2)
        remove_clone(clone_path)
        raise typer.Exit(2)

    # Symlink
    try:
        config.skills_path.mkdir(parents=True, exist_ok=True)
        create_symlink(skill_source, symlink_target)
        if not json_output and not quiet:
            print_success(f"Linked → [yellow]{symlink_target}[/]")
    except PermissionError:
        print_error(
            f"Cannot create symlink: {symlink_target}",
            json_output=json_output,
            code=1,
            hint=(
                "Permission denied. Try:\n"
                "  skillctl config set skills_dir ~/my-skills"
            ),
        )
        remove_clone(clone_path)
        raise typer.Exit(1)

    # Count and validate SKILL.md presence
    skill_mds = list(skill_source.rglob("SKILL.md"))
    if not skill_mds:
        if not json_output and not quiet:
            print_warning(
                f"No SKILL.md found in {repo}."
                " This repo may not be a valid skill."
            )

    # Register
    manifest.add_skill(
        slug,
        {
            "name": slug,
            "slug": slug,
            "source": "github",
            "repo": repo,
            "path": str(symlink_target),
            "clone_path": str(clone_path),
            "sub_path": path or ".",
            "commit": commit,
            "skills_count": len(skill_mds),
        },
    )

    if not json_output and not quiet:
        console.print(
            InstallReceipt(
                repo=repo,
                clone_path=str(clone_path),
                symlink_path=str(symlink_target),
                commit=commit,
                skill_count=len(skill_mds),
            )
        )
    elif json_output:
        result = {
            "status": "installed",
            "name": slug,
            "source": repo,
            "path": str(symlink_target),
            "skill_md": str(symlink_target / "SKILL.md"),
            "commit": commit,
        }
        next_actions = [
            f"cat {symlink_target / 'SKILL.md'}",
            f"skillctl info {slug} --json",
            "skillctl list --json",
        ]
        print_json(result, next_actions=next_actions)


def _handle_reinstall(
    slug: str,
    clone_path: Path,
    existing: dict,
    json_output: bool,
    quiet: bool,
    token: Optional[str] = None,
) -> None:
    """Handle re-install of an already installed skill."""
    from .importer.git_ops import is_git_repo, pull_repo

    if clone_path.exists() and is_git_repo(clone_path):
        if not json_output and not quiet:
            print_info("Already installed. Checking for updates...")
        try:
            old_sha, new_sha = pull_repo(clone_path, token=token)
            if old_sha != new_sha:
                manifest.update_skill(slug, {"commit": new_sha})
                if json_output:
                    print_json(
                        {
                            "status": "updated",
                            "name": slug,
                            "old_commit": old_sha,
                            "new_commit": new_sha,
                        }
                    )
                elif not quiet:
                    print_success(f"Updated {old_sha} → {new_sha}")
            else:
                if json_output:
                    print_json(
                        {
                            "status": "already_installed",
                            "name": slug,
                            "commit": old_sha,
                        }
                    )
                elif not quiet:
                    print_success(
                        f"Already up to date ({old_sha})"
                    )
        except RuntimeError as e:
            print_error(str(e), json_output=json_output, code=1)
    else:
        if json_output:
            print_json(
                {"status": "already_installed", "name": slug}
            )
        elif not quiet:
            print_success(f"Already installed: {slug}")


def _install_dry_run(
    repo: str,
    clone_path: Path,
    skill_source: Path,
    symlink_target: Path,
    slug: str,
    json_output: bool,
) -> None:
    """Show dry-run preview for install."""
    from .renderables import DryRunPreview

    actions = [
        {"action": "clone", "repo": repo, "dest": str(clone_path)},
        {
            "action": "symlink",
            "source": str(skill_source),
            "target": str(symlink_target),
        },
        {"action": "register", "name": slug},
    ]
    if json_output:
        print_json({"dry_run": True, "actions": actions})
    else:
        console.print(DryRunPreview(actions))


# ══════════════════════════════════════════════
# LIST (P0-3: --quiet, P1-5: timestamp column)
# ══════════════════════════════════════════════


@app.command(name="list")
def list_skills(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    fields: Annotated[
        Optional[str],
        typer.Option("--fields", help="Comma-separated fields (JSON only)"),
    ] = None,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Bare skill names, one per line")
    ] = False,
):
    """Show all installed skills."""
    from .renderables import InventoryLedger

    skills = manifest.list_skills()

    # --quiet: bare names for piping
    if quiet:
        for s in skills:
            print(s.get("slug", s.get("name", "")))
        return

    if json_output:
        output = filter_fields(skills, fields)
        next_actions = []
        if skills:
            next_actions.append(
                f"skillctl info {skills[0]['slug']} --json"
            )
        next_actions.append(
            'skillctl search "" --source=github --json'
        )
        print_json(output, next_actions=next_actions)
        return

    if not skills:
        console.print("\n  [dim]No skills installed yet.[/]")
        console.print(
            '  [dim]Try:[/] [bold]skillctl search[/] [yellow]"pdf"[/]'
        )
        console.print()
        return

    console.print()
    console.print(InventoryLedger(skills))
    console.print()


# ══════════════════════════════════════════════
# CREATE (P1-6: expected_pattern)
# ══════════════════════════════════════════════


@app.command()
def create(
    slug: Annotated[
        str,
        typer.Argument(
            help="Skill directory name (alphanumeric, hyphens, underscores)"
        ),
    ],
    name: Annotated[
        Optional[str], typer.Option("--name", help="Display name")
    ] = None,
    desc: Annotated[
        Optional[str], typer.Option("--desc", help="Description")
    ] = None,
    tags_str: Annotated[
        Optional[str],
        typer.Option("--tags", help="Tags (comma-separated)"),
    ] = None,
    author: Annotated[
        Optional[str], typer.Option("--author", help="Author name")
    ] = None,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip prompts")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Scaffold a new skill."""
    from .scaffold.creator import create_skill

    if not SLUG_PATTERN.match(slug):
        print_error(
            f"Invalid skill name: {slug}."
            " Use alphanumeric, hyphens, underscores only.",
            json_output=json_output,
            code=2,
            expected_pattern=SLUG_PATTERN_STR,
        )
        raise typer.Exit(2)

    # Interactive mode
    if not yes and not json_output:
        if name is None:
            name = typer.prompt("  Display name", default=slug)
        if desc is None:
            desc = typer.prompt("  Description", default="")
        if tags_str is None:
            tags_str = typer.prompt("  Tags (comma-sep)", default="")
        if author is None:
            author = typer.prompt("  Author", default="")

    # Defaults for non-interactive
    name = name or slug
    desc = desc or ""
    tags = [t.strip() for t in (tags_str or "").split(",") if t.strip()]
    author = author or ""

    try:
        result = create_skill(
            slug=slug,
            name=name,
            description=desc,
            tags=tags,
            author=author,
        )
    except FileExistsError as e:
        print_error(str(e), json_output=json_output, code=1)
        raise typer.Exit(1)

    if json_output:
        next_actions = [
            f"cat {result['skill_md']}",
            f"skillctl info {slug} --json",
        ]
        print_json(result, next_actions=next_actions)
    else:
        print_success(f"Created [yellow]{result['path']}[/]")
        print_success("Generated [yellow]SKILL.md[/]")
        print_success("Registered in manifest")
        console.print()
        console.print("  [bold green]Done![/] Edit your skill:")
        console.print(f"  [bold]$EDITOR {result['skill_md']}[/]")
        console.print()


# ══════════════════════════════════════════════
# UPDATE
# ══════════════════════════════════════════════


@app.command()
def update(
    name: Annotated[
        Optional[str],
        typer.Argument(
            help="Skill to update",
            autocompletion=_git_installed_names,
        ),
    ] = None,
    all_skills: Annotated[
        bool, typer.Option("--all", help="Update all git-installed skills")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress progress")
    ] = False,
):
    """Pull latest versions for git-installed skills."""
    from .importer.git_ops import is_git_repo, pull_repo

    config = load_config()

    if not name and not all_skills:
        print_error(
            "Specify a skill name or use --all",
            json_output=json_output,
            code=2,
            hint="Usage: skillctl update <name> or skillctl update --all",
        )
        raise typer.Exit(2)

    skills = manifest.list_skills()

    if name:
        target_skills = [s for s in skills if s.get("slug") == name]
        if not target_skills:
            print_error(
                f"Skill not found: {name}",
                json_output=json_output,
                code=2,
            )
            raise typer.Exit(2)
    else:
        target_skills = skills

    results = []
    for skill in target_skills:
        slug = skill.get("slug", "")

        if skill.get("source") != "github":
            if not json_output and not quiet:
                console.print(
                    f"  [dim]⊘[/] [blue]{slug}[/]"
                    "   [dim]local — skipped[/]"
                )
            results.append(
                {"name": slug, "status": "skipped", "reason": "local"}
            )
            continue

        clone_path = Path(skill.get("clone_path", ""))
        if not clone_path.exists() or not is_git_repo(clone_path):
            if not json_output:
                print_error(f"Clone not found for {slug}")
            results.append(
                {
                    "name": slug,
                    "status": "error",
                    "message": "clone not found",
                }
            )
            continue

        try:
            old_sha, new_sha = pull_repo(clone_path, token=config.github_token)
            if old_sha != new_sha:
                manifest.update_skill(slug, {"commit": new_sha})
                if not json_output and not quiet:
                    print_success(
                        f"[blue]{slug}[/]"
                        f"   [dim]{old_sha} → {new_sha}[/]"
                        "  [green]updated[/]"
                    )
                results.append(
                    {
                        "name": slug,
                        "status": "updated",
                        "old_commit": old_sha,
                        "new_commit": new_sha,
                    }
                )
            else:
                if not json_output and not quiet:
                    print_success(
                        f"[blue]{slug}[/]"
                        "   [dim]already up to date[/]"
                    )
                results.append(
                    {
                        "name": slug,
                        "status": "current",
                        "commit": old_sha,
                    }
                )
        except RuntimeError as e:
            if not json_output:
                print_error(f"{slug}: {e}")
            results.append(
                {
                    "name": slug,
                    "status": "error",
                    "message": str(e),
                }
            )

    if json_output:
        print_json(results)
    elif not quiet:
        updated = sum(
            1 for r in results if r.get("status") == "updated"
        )
        checked = sum(
            1
            for r in results
            if r.get("status") in ("updated", "current")
        )
        local = sum(
            1 for r in results if r.get("status") == "skipped"
        )
        console.print(
            f"\n  [dim]{checked} checked, {updated} updated,"
            f" {local} local (skipped)[/]"
        )
        console.print()


# ══════════════════════════════════════════════
# REMOVE (P0-4: ref-counted clones, P1-7: clone_kept)
# ══════════════════════════════════════════════


@app.command()
def remove(
    name: Annotated[
        str,
        typer.Argument(
            help="Skill to remove",
            autocompletion=_installed_names,
        ),
    ],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without executing"),
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Remove an installed skill."""
    from .importer.linker import remove_clone, remove_symlink
    from .renderables import DryRunPreview

    skill = manifest.get_skill(name)

    if not skill:
        print_error(
            f"Skill not found: {name}",
            json_output=json_output,
            code=2,
        )
        raise typer.Exit(2)

    symlink_path = Path(skill.get("path", ""))
    clone_path = (
        Path(skill["clone_path"]) if skill.get("clone_path") else None
    )

    # Reference counting: check if other skills share this clone
    clone_shared = False
    siblings: list[str] = []
    if clone_path and skill.get("clone_path"):
        siblings = _skills_sharing_clone(
            skill["clone_path"], name
        )
        clone_shared = len(siblings) > 0

    actions = []
    if symlink_path.is_symlink():
        actions.append({"action": "unlink", "path": str(symlink_path)})
    if clone_path and clone_path.exists() and not clone_shared:
        actions.append(
            {"action": "delete_clone", "path": str(clone_path)}
        )
    elif clone_path and clone_shared:
        actions.append(
            {
                "action": "keep_clone",
                "path": str(clone_path),
                "reason": f"{len(siblings)} other skill(s) installed from same repo",
            }
        )
    actions.append({"action": "unregister", "name": name})

    # Dry-run
    if dry_run:
        if json_output:
            print_json({"dry_run": True, "actions": actions})
        else:
            console.print(
                "\n  [purple]DRY RUN[/]"
                " [dim]— no changes will be made[/]"
            )
            for a in actions:
                target = a.get("path", a.get("name", ""))
                console.print(
                    f"  [dim]Would {a['action']}[/] {target}"
                )
            console.print()
        return

    # Confirm
    if not yes and not json_output:
        console.print("\n  [dim]This will:[/]")
        if symlink_path.is_symlink():
            console.print(
                f"    [dim]• Remove symlink from[/]"
                f" [yellow]{symlink_path}[/]"
            )
        if clone_path and clone_path.exists() and not clone_shared:
            console.print(
                f"    [dim]• Delete clone from[/]"
                f" [yellow]{clone_path}[/]"
            )
        elif clone_shared:
            console.print(
                f"    [dim]• Keep clone[/] [yellow]{clone_path}[/]"
                f" [dim]({len(siblings)} other skill(s) use it)[/]"
            )
        console.print("    [dim]• Remove from manifest[/]")
        console.print()

        if not typer.confirm("  Continue?", default=False):
            console.print("  [dim]Cancelled.[/]")
            raise typer.Exit(0)

    # Execute
    if symlink_path.is_symlink():
        remove_symlink(symlink_path)

    if clone_path and clone_path.exists() and not clone_shared:
        remove_clone(clone_path)

    is_local = skill.get("source") != "github"
    files_remain = (
        is_local
        and symlink_path.exists()
        and not symlink_path.is_symlink()
    )

    manifest.remove_skill(name)

    if json_output:
        result: dict = {"status": "removed", "name": name}
        if clone_shared:
            result["clone_kept"] = True
            result["reason"] = (
                f"{len(siblings)} other skill(s) installed"
                f" from same repo: {', '.join(siblings)}"
            )
        if files_remain:
            result["note"] = f"Files remain at {symlink_path}"
        print_json(result)
    else:
        print_success(f"Removed [blue]{name}[/]")
        if clone_shared:
            print_dim(
                f"Clone kept at [yellow]{clone_path}[/]"
                f" [dim]({len(siblings)} other skill(s) use it)[/]"
            )
        if files_remain:
            print_dim(
                f"Files remain at [yellow]{symlink_path}[/]"
                " (local skill — not deleted)"
            )
        console.print()


# ══════════════════════════════════════════════
# INFO
# ══════════════════════════════════════════════


@app.command()
def info(
    name: Annotated[
        str,
        typer.Argument(
            help="Skill name or user/repo",
            autocompletion=_installed_names,
        ),
    ],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    fields: Annotated[
        Optional[str],
        typer.Option("--fields", help="Comma-separated fields (JSON only)"),
    ] = None,
):
    """Show details of a specific skill."""
    from .discovery.github import GitHubRateLimitError, get_repo_info
    from .renderables import SkillCard

    config = load_config()

    # Check installed skills first
    skill = manifest.get_skill(name)
    if skill:
        _show_installed_info(skill, name, json_output, fields)
        return

    # Try GitHub lookup
    if REPO_PATTERN.match(name):
        try:
            repo_info = get_repo_info(config, name)
        except GitHubRateLimitError as e:
            print_error(str(e), json_output=json_output, code=1)
            raise typer.Exit(1)
        if repo_info:
            _show_github_info(repo_info, name, json_output, fields)
            return

    print_error(
        f"Skill not found: {name}", json_output=json_output, code=2
    )
    raise typer.Exit(2)


def _show_installed_info(
    skill: dict,
    name: str,
    json_output: bool,
    fields: Optional[str],
) -> None:
    from .renderables import SkillCard

    if json_output:
        output = filter_fields(skill, fields)
        next_actions = [
            f"cat {skill.get('path', '')}/SKILL.md",
            f"skillctl remove {name} -y --json",
        ]
        if skill.get("source") == "github":
            next_actions.insert(
                1, f"skillctl update {name} --json"
            )
        print_json(output, next_actions=next_actions)
    else:
        console.print(SkillCard(skill, name))


def _show_github_info(
    repo_info: dict,
    name: str,
    json_output: bool,
    fields: Optional[str],
) -> None:
    if json_output:
        output = filter_fields(repo_info, fields)
        next_actions = [
            f"skillctl install {name} -y --json",
        ]
        print_json(output, next_actions=next_actions)
    else:
        console.print()
        console.print(
            f"  [bold blue]{repo_info['name']}[/]"
            f" [dim]— {repo_info.get('description', '')}[/]"
        )
        console.print()
        if repo_info.get("tags"):
            tags_str = "  ".join(
                f"[purple]{t}[/]" for t in repo_info["tags"]
            )
            console.print(f"  [dim]Tags[/]         {tags_str}")
        if repo_info.get("stars"):
            console.print(
                f"  [dim]Stars[/]        [yellow]★ {repo_info['stars']}[/]"
            )
        if repo_info.get("updated"):
            console.print(
                f"  [dim]Updated[/]      [yellow]{repo_info['updated']}[/]"
            )
        if repo_info.get("license"):
            console.print(
                f"  [dim]License[/]      [yellow]{repo_info['license']}[/]"
            )
        console.print(
            "  [dim]Status[/]       [dim]○ not installed[/]"
        )
        if repo_info.get("url"):
            console.print(
                f"  [dim]URL[/]          [blue underline]{repo_info['url']}[/]"
            )
        console.print()
        console.print(
            f"  [dim]Install:[/]"
            f" [bold]skillctl install[/] [blue]{name}[/]"
        )
        console.print()


# ══════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════

config_app = typer.Typer(help="View and set configuration.")
app.add_typer(config_app, name="config")


@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context):
    """View current configuration."""
    if ctx.invoked_subcommand is not None:
        return

    config = load_config()
    has_gh = config.github_token is not None

    console.print()
    console.print(
        f"  [bold blue]Configuration[/] [dim]{CONFIG_PATH}[/]"
    )
    console.print()
    console.print(
        f"  [dim]skills_dir[/]      [yellow]{config.skills_dir}[/]",
        end="",
    )
    if config.skills_dir == str(Path.home() / ".claude" / "skills"):
        console.print("         [dim](default)[/]")
    else:
        console.print()

    console.print(
        f"  [dim]repos_dir[/]       [yellow]{config.repos_dir}[/]",
        end="",
    )
    default_repos = str(Path.home() / ".skillctl" / "repos")
    if config.repos_dir == default_repos:
        console.print("        [dim](default)[/]")
    else:
        console.print()

    if config.scan_paths:
        console.print(
            f"  [dim]scan_paths[/]      [yellow]{', '.join(config.scan_paths)}[/]"
        )
    else:
        console.print("  [dim]scan_paths[/]      [dim]—[/]")

    console.print(
        f"  [dim]registries[/]      [yellow]{', '.join(config.registries)}[/]"
    )

    if has_gh:
        console.print(
            "  [dim]github.token[/]"
            "    [green]● via gh auth[/]"
            "             [dim](auto-detected)[/]"
        )
    else:
        console.print(
            "  [dim]github.token[/]"
            "    [dim]○ not configured[/]"
        )

    console.print(
        f"  [dim]default_format[/]  [yellow]{config.default_format}[/]"
        "                    [dim](default)[/]"
    )
    console.print(
        f"  [dim]cache_ttl[/]       [yellow]{config.cache_ttl}s[/]"
        "                    [dim](default)[/]"
    )
    console.print()
    console.print(
        "  [dim]Set a value:[/]"
        " [bold]skillctl config set[/] [cyan]<key>[/] [cyan]<value>[/]"
    )
    console.print()


@config_app.command(name="set")
def config_set(
    key: Annotated[str, typer.Argument(help="Config key")],
    value: Annotated[str, typer.Argument(help="Config value")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Set a configuration value."""
    try:
        set_config_value(key, value)
        if json_output:
            print_json({"status": "set", "key": key, "value": value})
        else:
            print_success(f"[dim]{key}[/] → [yellow]{value}[/]")
    except ValueError as e:
        print_error(
            str(e),
            json_output=json_output,
            code=2,
            valid_flags=VALID_KEYS,
        )
        raise typer.Exit(2)


@config_app.command(name="get")
def config_get(
    key: Annotated[str, typer.Argument(help="Config key")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Get a configuration value."""
    config = load_config()

    value_map: dict = {
        "skills_dir": config.skills_dir,
        "repos_dir": config.repos_dir,
        "scan_paths": config.scan_paths,
        "github_token": "●" if config.github_token else None,
        "default_format": config.default_format,
        "cache_ttl": config.cache_ttl,
    }

    if key not in value_map:
        print_error(
            f"Unknown config key: {key}",
            json_output=json_output,
            code=2,
            valid_flags=VALID_KEYS,
        )
        raise typer.Exit(2)

    if json_output:
        print_json({"key": key, "value": value_map[key]})
    else:
        val = value_map[key]
        print(val if val is not None else "")


# ══════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
# LINT
# ══════════════════════════════════════════════


@app.command()
def lint(
    name: Annotated[
        str,
        typer.Argument(
            help="Skill name, path, or example name",
            autocompletion=_installed_names,
        ),
    ],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Score and validate a skill against best practices."""
    from .lint import lint_skill, lint_result_to_dict
    from .learn.renderer import render_lint_result

    config = load_config()

    # Resolve skill path: installed skill → local path → example
    skill = manifest.get_skill(name)
    if skill:
        skill_path = Path(skill["path"])
    elif Path(name).exists():
        skill_path = Path(name)
    else:
        # Try as example
        from .learn.loader import EXAMPLES_DIR

        example_path = EXAMPLES_DIR / f"{name}.md"
        if example_path.exists():
            skill_path = example_path
        else:
            print_error(
                f"Skill not found: {name}",
                json_output=json_output,
                code=2,
            )
            raise typer.Exit(2)

    result = lint_skill(skill_path)
    result_dict = lint_result_to_dict(result)

    if json_output:
        next_actions = []
        if result.score < result.max_score:
            next_actions.append(
                f"Edit {result.path} to fix issues, then: "
                f"skillctl lint {name} --json"
            )
        next_actions.append(f"skillctl info {name} --json")
        print_json(result_dict, next_actions=next_actions)
    else:
        render_lint_result(result_dict)


registry_app = typer.Typer(help="Manage trusted skill registries.")
app.add_typer(registry_app, name="registry")


@registry_app.callback(invoke_without_command=True)
def registry_callback(ctx: typer.Context):
    """Show configured registries. Use subcommands to modify."""
    if ctx.invoked_subcommand is not None:
        return
    # Default: same as `registry list`
    _registry_list_impl(json_output=False)


def _registry_list_impl(json_output: bool = False) -> None:
    from .discovery.registry import fetch_registry

    config = load_config()

    if json_output:
        entries = []
        for reg in config.registries:
            cached = fetch_registry(config, reg)
            enriched = any(s.get("keywords") for s in cached)
            entries.append({
                "registry": reg,
                "skills": len(cached),
                "enriched": enriched,
            })
        print_json(entries)
        return

    console.print()
    for reg in config.registries:
        cached = fetch_registry(config, reg)
        enriched = any(s.get("keywords") for s in cached)
        status = "[green]enriched[/]" if enriched else "[dim]not enriched[/]"
        console.print(
            f"  [green bold]{reg}[/]"
            f"  [dim]{len(cached)} skills[/]"
            f"  {status}"
        )
    console.print()


@registry_app.command(name="list")
def registry_list(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """List all configured registries."""
    _registry_list_impl(json_output)


@registry_app.command(name="add")
def registry_add(
    repo: Annotated[
        str, typer.Argument(help="GitHub repo (user/repo)")
    ],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Add a trusted registry. Validates the repo has skills."""
    if not REPO_PATTERN.match(repo):
        print_error(
            f"Invalid repo format: {repo}. Expected: user/repo",
            json_output=json_output,
            code=2,
            expected_pattern=REPO_PATTERN_STR,
        )
        raise typer.Exit(2)

    config = load_config()

    if repo in config.registries:
        if json_output:
            print_json({"status": "already_exists", "registry": repo})
        else:
            print_info(f"Already configured: [green]{repo}[/]")
        return

    # Validate: must be a real registry (multiple skills in subdirs)
    from .discovery.registry import validate_registry, fetch_registry

    if not json_output:
        console.print(f"  [dim]Verifying {repo}...[/]")

    result = validate_registry(config, repo)

    if not result["valid"]:
        print_error(
            result["reason"],
            json_output=json_output,
            code=2,
        )
        if result.get("suggestion"):
            if json_output:
                pass  # already in error JSON
            else:
                print_dim(
                    f"Try: [bold]{result['suggestion']}[/]"
                )
        raise typer.Exit(2)

    # Fetch + enrich the skills
    skills = fetch_registry(config, repo)

    # Add to config
    config.registries.append(repo)
    from .config import save_config
    save_config(config)

    if json_output:
        print_json({
            "status": "added",
            "registry": repo,
            "skills": len(skills),
            "registries": config.registries,
        })
    else:
        print_success(
            f"Verified [green]{repo}[/]"
            f" ({len(skills)} skills found)"
        )
        print_success("Added to registries")
        console.print()
        for reg in config.registries:
            marker = "  [green]← new[/]" if reg == repo else ""
            console.print(f"  [yellow]{reg}[/]{marker}")
        console.print()


@registry_app.command(name="remove")
def registry_remove(
    repo: Annotated[
        str, typer.Argument(help="Registry to remove")
    ],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Remove a registry from the configured list."""
    config = load_config()

    if repo not in config.registries:
        print_error(
            f"Registry not found: {repo}",
            json_output=json_output,
            code=2,
        )
        raise typer.Exit(2)

    config.registries.remove(repo)
    from .config import save_config
    save_config(config)

    # Clear cache for removed registry
    from .discovery.registry import _cache_path
    cache = _cache_path(repo)
    if cache.exists():
        cache.unlink()

    if json_output:
        print_json({
            "status": "removed",
            "registry": repo,
            "registries": config.registries,
        })
    else:
        print_success(f"Removed [blue]{repo}[/]")
        print_dim("Cache cleared")
        console.print()


@registry_app.command(name="reset")
def registry_reset(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """Reset registries to defaults."""
    from .config import DEFAULT_REGISTRIES, save_config

    config = load_config()
    config.registries = list(DEFAULT_REGISTRIES)
    save_config(config)

    if json_output:
        print_json({
            "status": "reset",
            "registries": config.registries,
        })
    else:
        print_success("Reset to default registries")
        console.print()
        for reg in config.registries:
            console.print(f"  [yellow]{reg}[/]")
        console.print()


# ── Entry point ──


def main():
    app()
