"""Custom Rich renderables — skillctl's visual language."""

from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from rich.text import Text

from .output import relative_time


class SearchLedger:
    """Borderless search results table with dot language."""

    def __init__(self, results: list[dict], total: int):
        self.results = results
        self.total = total

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        table = Table(show_header=True, box=None, padding=(0, 2))
        table.add_column("", width=1)
        table.add_column("Name", style="green bold")
        table.add_column("Source", style="cyan")
        table.add_column("Description")
        table.add_column("★", style="yellow", justify="right")

        for r in self.results:
            dot = "[green]●[/]" if r.get("installed") else "[dim]○[/]"
            stars = f"★ {r['stars']}" if r.get("stars") else ""
            # Prefer LLM-generated short_desc over raw description
            desc = r.get("short_desc") or r.get("description") or ""
            if len(desc) > 80 and not r.get("short_desc"):
                desc = desc[:77] + "..."
            table.add_row(
                dot,
                r.get("name", r.get("slug", "")),
                r.get("source", ""),
                desc,
                stars,
            )

        yield table

        showing = (
            f"Showing {len(self.results)} of {self.total}"
            if self.total > len(self.results)
            else f"Showing {len(self.results)} results"
        )
        yield Text(
            f"\n  ● installed  ○ available     {showing}",
            style="dim",
        )


class InventoryLedger:
    """Borderless installed-skills table with timestamps."""

    def __init__(self, skills: list[dict]):
        self.skills = skills

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        table = Table(show_header=True, box=None, padding=(0, 2))
        table.add_column("Name", style="green bold")
        table.add_column("Source", style="cyan")
        table.add_column("Installed")

        for s in self.skills:
            source_display = (
                s.get("repo", "local")
                if s.get("source") == "github"
                else "local"
            )
            installed_at = relative_time(s.get("installed_at", ""))
            table.add_row(
                s.get("slug", s.get("name", "")),
                source_display,
                f"[dim]{installed_at}[/]"
                if installed_at
                else "[dim]—[/]",
            )

        yield table

        github_count = sum(
            1 for s in self.skills if s.get("source") == "github"
        )
        local_count = len(self.skills) - github_count
        yield Text(
            f"\n  {len(self.skills)} skills installed"
            f" ({github_count} from GitHub, {local_count} local)",
            style="dim",
        )


class SkillCard:
    """Key-value skill info card. No borders."""

    def __init__(self, skill: dict, name: str):
        self.skill = skill
        self.name = name

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        s = self.skill
        yield Text()

        title = Text("  ")
        title.append(s.get("name", self.name), style="bold blue")
        title.append(f" — {s.get('description', '')}", style="dim")
        yield title
        yield Text()

        fields = [
            ("Author", s.get("author"), "yellow"),
            ("Tags", None, "magenta"),
            ("Repo", s.get("repo"), "blue"),
            ("Commit", s.get("commit"), "dim"),
            ("Source", s.get("source", "unknown"), "cyan"),
            ("Path", s.get("path", ""), "yellow"),
            ("Status", "● installed", "green"),
        ]

        for label, value, style in fields:
            if label == "Tags":
                tag_list = s.get("tags", [])
                if tag_list:
                    line = Text(f"  {label:<13}")
                    line.style = "dim"
                    for i, t in enumerate(tag_list):
                        if i > 0:
                            line.append("  ")
                        line.append(t, style="magenta")
                    yield line
            elif value:
                line = Text(f"  {label:<13}")
                line.style = "dim"
                line.append(str(value), style=style)
                yield line

        yield Text()


class InstallReceipt:
    """Post-install confirmation. Three checkmarks + metadata."""

    def __init__(
        self,
        repo: str,
        clone_path: str,
        symlink_path: str,
        commit: str,
        skill_count: int,
    ):
        self.repo = repo
        self.clone_path = clone_path
        self.symlink_path = symlink_path
        self.commit = commit
        self.skill_count = skill_count

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Text()

        line1 = Text("  ✓ ", style="green")
        line1.append("Cloned ", style="")
        line1.append(self.repo, style="blue")
        line1.append(" → ", style="")
        line1.append(self.clone_path, style="dim")
        yield line1

        line2 = Text("  ✓ ", style="green")
        line2.append("Linked → ", style="")
        line2.append(self.symlink_path, style="yellow")
        yield line2

        yield Text("  ✓ Registered in manifest", style="green")
        yield Text()
        yield Text("  Installed!", style="bold green")
        yield Text(
            "  Skill is now available to your agent.", style="dim"
        )

        if self.skill_count:
            yield Text(
                f"\n  Contains:  {self.skill_count} skill(s)",
                style="dim",
            )
        yield Text(f"  Commit:    {self.commit}", style="dim")
        yield Text()


class DryRunPreview:
    """Purple-labeled preview of actions. Used by install/remove --dry-run."""

    def __init__(self, actions: list[dict]):
        self.actions = actions

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Text()

        header = Text("  DRY RUN", style="bold magenta")
        header.append(" — no changes will be made", style="dim")
        yield header
        yield Text()

        for a in self.actions:
            action = a.get("action", "")
            target = a.get("path", a.get("name", ""))

            if a.get("repo"):
                line = Text("  Would clone      ", style="dim")
                line.append(a["repo"], style="blue")
                line.append(" → ", style="dim")
                line.append(a.get("dest", ""), style="dim")
            elif action == "symlink":
                line = Text("  Would link       ", style="dim")
                line.append(a.get("target", ""), style="yellow")
            elif action in ("register", "unregister"):
                line = Text(f"  Would {action:<10} ", style="dim")
                line.append(target)
            elif action == "keep_clone":
                line = Text("  Would keep       ", style="dim")
                line.append(target, style="yellow")
                if a.get("reason"):
                    line.append(f" ({a['reason']})", style="dim")
            elif action == "unlink":
                line = Text("  Would unlink     ", style="dim")
                line.append(target, style="yellow")
            elif action == "delete_clone":
                line = Text("  Would delete     ", style="dim")
                line.append(target, style="yellow")
            else:
                line = Text(f"  Would {action:<10} ", style="dim")
                line.append(str(target), style="yellow")

            yield line

        yield Text()


class ErrorCard:
    """Styled error with optional hint. Always to stderr."""

    def __init__(
        self,
        message: str,
        hint: str | None = None,
    ):
        self.message = message
        self.hint = hint

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Text(f"  ✗ {self.message}", style="red")
        if self.hint:
            yield Text(f"  {self.hint}", style="dim")
