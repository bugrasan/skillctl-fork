"""Visual rendering engine for learn topics.

Visual-first: diagrams, panels, and color-coded examples.
Text-second: explanations support the visuals.
"""

import re

from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich import box

from ..output import console, err_console
from .loader import list_examples, list_topics, load_example, load_topic

# ── Style constants (match theme.py semantics) ──

LAYER_STYLES = [
    ("green", "identity"),
    ("cyan", "when"),
    ("yellow", "rules"),
    ("red", "avoid"),
    ("blue", "show"),
]

TOPIC_ICONS = {
    "anatomy": "1",
    "write": "2",
    "organize": "3",
    "examples": "4",
}


# ══════════════════════════════════════════════
# INDEX
# ══════════════════════════════════════════════


def render_index(json_output: bool = False) -> dict | None:
    """Render the learn dashboard."""
    topics = list_topics()

    if json_output:
        return {
            "topics": topics,
            "next_actions": [
                "skillctl learn anatomy --json",
                "skillctl learn write --json",
                "skillctl learn organize --json",
                "skillctl learn examples --json",
            ],
        }

    console.print()

    # Header
    header = Text()
    header.append("  LEARN", style="bold")
    header.append("  ", style="")
    header.append("Master the art of writing agent skills", style="dim")
    console.print(header)
    console.print()

    # Topic list as a clean table
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        pad_edge=True,
    )
    table.add_column("", width=4, justify="right")
    table.add_column("Topic", style="bold", min_width=12)
    table.add_column("Description", style="dim")

    for i, topic in enumerate(topics, 1):
        table.add_row(
            f"[dim]{i}[/]",
            f"[green]{topic['slug']}[/]",
            topic["subtitle"],
        )

    # Add lint as a bonus entry
    table.add_row("", "", "")
    table.add_row(
        "[dim]+[/]",
        "[yellow]lint[/]",
        "Score & validate your skills",
    )

    console.print(Padding(table, (0, 2)))
    console.print()

    console.print(
        "  [dim]Start with:[/]  [bold]skillctl learn anatomy[/]"
    )
    console.print()
    return None


# ══════════════════════════════════════════════
# ANATOMY
# ══════════════════════════════════════════════


def render_anatomy(json_output: bool = False) -> dict | None:
    """Render the skill anatomy visual."""
    data = load_topic("anatomy")
    fm = data["frontmatter"]
    topics = list_topics()

    if json_output:
        return {
            "topic": "anatomy",
            "title": fm.get("title", ""),
            "intro": data["intro"],
            "layers": [
                {
                    "number": i + 1,
                    "name": s["title"],
                    "label": s["label"],
                    "description": s["content"],
                    "example": s["subsections"].get("example", ""),
                    "points": _parse_points(
                        s["subsections"].get("points", "")
                    ),
                }
                for i, s in enumerate(data["sections"])
            ],
            "next_actions": [
                "skillctl learn write --json",
                'skillctl create my-skill --name "My Skill" -y --json',
            ],
        }

    _print_topic_header(fm, topics)
    console.print(f"  [dim]{data['intro']}[/]")
    console.print()

    for i, section in enumerate(data["sections"]):
        style_color, style_label = LAYER_STYLES[
            i % len(LAYER_STYLES)
        ]

        # Build panel content
        parts: list[Text | Syntax | Padding] = []

        # Code example
        example = section["subsections"].get("example", "")
        if example:
            lang, code = _extract_code_block(example)
            if code:
                parts.append(
                    Syntax(
                        code,
                        lang or "markdown",
                        theme="monokai",
                        padding=0,
                    )
                )
                parts.append(Text())

        # Description
        if section["content"]:
            parts.append(Text(section["content"], style="dim"))
            parts.append(Text())

        # Key points
        points = section["subsections"].get("points", "")
        if points:
            for point in _parse_points(points):
                line = Text()
                line.append("  \u25b8 ", style=style_color)
                line.append(point)
                parts.append(line)

        # Panel title
        num = i + 1
        label = section.get("label", style_label)
        title = (
            f"[bold {style_color}]{num}[/]"
            f" [bold]{section['title'].upper()}[/]"
            f" [dim]\u2500\u2500 {label}[/]"
        )

        panel = Panel(
            Group(*parts),
            title=title,
            title_align="left",
            border_style=style_color,
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(Padding(panel, (0, 2)))

        # Connector arrow (except after last)
        if i < len(data["sections"]) - 1:
            console.print("                    [dim]\u2502[/]")
            console.print("                    [dim]\u25bc[/]")

    console.print()
    _print_nav_footer(fm, topics)
    return None


# ══════════════════════════════════════════════
# WRITE
# ══════════════════════════════════════════════


def render_write(json_output: bool = False) -> dict | None:
    """Render the writing guide with do/don't comparisons."""
    data = load_topic("write")
    fm = data["frontmatter"]
    topics = list_topics()

    if json_output:
        return {
            "topic": "write",
            "title": fm.get("title", ""),
            "intro": data["intro"],
            "rules": [
                {
                    "name": s["title"],
                    "description": s["content"],
                    "do": _parse_points(
                        s["subsections"].get("do", "")
                    ),
                    "dont": _parse_points(
                        s["subsections"].get("dont", "")
                    ),
                    "example": s["subsections"].get("example", ""),
                    "points": _parse_points(
                        s["subsections"].get("points", "")
                    ),
                }
                for s in data["sections"]
            ],
            "next_actions": [
                "skillctl learn organize --json",
                "skillctl learn anatomy --json",
            ],
        }

    _print_topic_header(fm, topics)
    console.print(f"  [dim]{data['intro']}[/]")
    console.print()

    for i, section in enumerate(data["sections"]):
        parts: list = []

        # Do/Don't comparison table
        do_items = _parse_points(section["subsections"].get("do", ""))
        dont_items = _parse_points(
            section["subsections"].get("dont", "")
        )

        if do_items and dont_items:
            table = Table(
                show_header=True,
                box=box.SIMPLE_HEAVY,
                padding=(0, 1),
                expand=True,
            )
            table.add_column(
                "\u2717 DON'T", style="red", ratio=1
            )
            table.add_column(
                "\u2713 DO", style="green", ratio=1
            )

            max_rows = max(len(dont_items), len(do_items))
            for j in range(max_rows):
                dont = dont_items[j] if j < len(dont_items) else ""
                do = do_items[j] if j < len(do_items) else ""
                table.add_row(dont, do)

            parts.append(table)

        # Description text
        if section["content"]:
            parts.append(Text())
            parts.append(Text(section["content"], style="dim"))

        # Code example
        example = section["subsections"].get("example", "")
        if example:
            lang, code = _extract_code_block(example)
            if code:
                parts.append(Text())
                parts.append(
                    Syntax(
                        code,
                        lang or "markdown",
                        theme="monokai",
                        padding=0,
                    )
                )

        # Points
        points_text = section["subsections"].get("points", "")
        if points_text:
            parts.append(Text())
            for point in _parse_points(points_text):
                line = Text()
                line.append("  \u25b8 ", style="cyan")
                line.append(point, style="dim")
                parts.append(line)

        title = f"[bold]RULE {i + 1}[/] [dim]\u2500\u2500[/] {section['title']}"

        panel = Panel(
            Group(*parts),
            title=title,
            title_align="left",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(Padding(panel, (0, 2)))
        console.print()

    _print_nav_footer(fm, topics)
    return None


# ══════════════════════════════════════════════
# ORGANIZE
# ══════════════════════════════════════════════


def render_organize(json_output: bool = False) -> dict | None:
    """Render the organization guide with tree diagrams."""
    data = load_topic("organize")
    fm = data["frontmatter"]
    topics = list_topics()

    if json_output:
        return {
            "topic": "organize",
            "title": fm.get("title", ""),
            "intro": data["intro"],
            "sections": [
                {
                    "name": s["title"],
                    "description": s["content"],
                    "points": _parse_points(
                        s["subsections"].get("points", "")
                    ),
                }
                for s in data["sections"]
            ],
            "next_actions": [
                "skillctl learn examples --json",
                "skillctl learn write --json",
            ],
        }

    _print_topic_header(fm, topics)
    console.print(f"  [dim]{data['intro']}[/]")
    console.print()

    for section in data["sections"]:
        parts: list = []

        # Tree diagram
        tree_text = section["subsections"].get("tree", "")
        if tree_text:
            tree = _build_tree(tree_text)
            if tree:
                parts.append(tree)
                parts.append(Text())

        # Table
        table_text = section["subsections"].get("table", "")
        if table_text:
            tbl = _parse_markdown_table(table_text)
            if tbl:
                parts.append(tbl)
                parts.append(Text())

        # Tags list
        tags_text = section["subsections"].get("tags", "")
        if tags_text:
            for line in _parse_points(tags_text):
                if ":" in line:
                    cat, vals = line.split(":", 1)
                    t = Text()
                    t.append(f"  {cat.strip()}: ", style="bold")
                    t.append(vals.strip(), style="magenta")
                    parts.append(t)
                else:
                    parts.append(Text(f"  {line}"))
            parts.append(Text())

        # Stages
        stages_text = section["subsections"].get("stages", "")
        if stages_text:
            for line in _parse_points(stages_text):
                parts.append(Text(f"  {line}", style="dim"))
            parts.append(Text())

        # Description
        if section["content"]:
            parts.append(Text(section["content"], style="dim"))
            parts.append(Text())

        # Points
        points_text = section["subsections"].get("points", "")
        if points_text:
            for point in _parse_points(points_text):
                line = Text()
                line.append("  \u25b8 ", style="yellow")
                line.append(point, style="dim")
                parts.append(line)

        panel = Panel(
            Group(*parts),
            title=f"[bold]{section['title']}[/]",
            title_align="left",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(Padding(panel, (0, 2)))
        console.print()

    _print_nav_footer(fm, topics)
    return None


# ══════════════════════════════════════════════
# EXAMPLES
# ══════════════════════════════════════════════


def render_examples(
    name: str | None = None, json_output: bool = False
) -> dict | None:
    """Render example list or a specific example skill."""
    if json_output:
        if name:
            ex = load_example(name)
            if not ex:
                return {
                    "status": "error",
                    "message": f"Example not found: {name}",
                }
            return {
                "example": name,
                "frontmatter": ex["frontmatter"],
                "content": ex["body"],
                "next_actions": [
                    f'skillctl create {name} --name "{ex["frontmatter"].get("name", name)}" -y --json'
                ],
            }
        examples = list_examples()
        return {
            "examples": examples,
            "next_actions": [
                f"skillctl learn examples {examples[0]['slug']} --json"
                if examples
                else "skillctl learn anatomy --json"
            ],
        }

    if name:
        ex = load_example(name)
        if not ex:
            return {"status": "error", "message": f"Example not found: {name}"}
        _render_single_example(name, ex)
    else:
        _render_example_list()

    return None


def _render_example_list() -> None:
    """Show available examples."""
    examples = list_examples()

    console.print()
    header = Text()
    header.append("  EXAMPLES", style="bold")
    header.append("  ", style="")
    header.append("Well-written skills to learn from", style="dim")
    console.print(header)
    console.print()

    for ex in examples:
        line = Text("    ")
        line.append(ex["slug"], style="green bold")
        line.append(f"  {ex['description']}", style="dim")
        console.print(line)

    console.print()
    if examples:
        console.print(
            f"  [dim]View one:[/]  [bold]skillctl learn examples"
            f" {examples[0]['slug']}[/]"
        )
    console.print()


def _render_single_example(name: str, ex: dict | None = None) -> bool:
    """Render a single example. Returns False if not found."""
    if ex is None:
        ex = load_example(name)
    if not ex:
        err_console.print(
            f"  [red]\u2717 Example not found: {name}[/]"
        )
        return False

    fm = ex["frontmatter"]
    console.print()

    # Header
    header = Text()
    header.append(
        f"  EXAMPLE: {fm.get('name', name).upper()}", style="bold"
    )
    console.print(header)
    console.print(
        f"  [dim]{fm.get('description', '')}[/]"
    )
    console.print()

    # Show the full SKILL.md with syntax highlighting
    panel = Panel(
        Syntax(
            ex["raw"],
            "markdown",
            theme="monokai",
            line_numbers=True,
            padding=0,
        ),
        title="[bold]SKILL.md[/]",
        title_align="left",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 1),
    )
    console.print(Padding(panel, (0, 2)))
    console.print()

    # Score hint
    console.print(
        "  [dim]Validate this pattern:[/]"
        f"  [bold]skillctl lint {name}[/]"
    )
    console.print(
        "  [dim]Create from this:[/]"
        f'     [bold]skillctl create {name}'
        f' --name "{fm.get("name", name)}"[/]'
    )
    console.print()


# ══════════════════════════════════════════════
# LINT RESULTS
# ══════════════════════════════════════════════


def render_lint_result(result: dict) -> None:
    """Render lint results with visual score bar."""
    score = result["score"]
    max_score = result["max_score"]
    slug = result["slug"]

    console.print()

    # Header with score
    header = Text()
    header.append(f"  {slug}", style="bold")
    pad = 40 - len(slug)
    header.append(" " * max(pad, 2))
    header.append(f"Score: {score}/{max_score}", style=_score_style(score))
    console.print(header)
    console.print()

    # Visual score bar
    bar_width = 30
    filled = int(bar_width * score / max_score) if max_score else 0
    bar = Text("  ")
    bar.append("\u2588" * filled, style=_score_style(score))
    bar.append("\u2591" * (bar_width - filled), style="dim")
    bar.append(f"  {score}%", style=_score_style(score))
    console.print(bar)
    console.print()

    # Individual checks
    for check in result["checks"]:
        if check["passed"]:
            line = Text("  ")
            line.append("\u2713 ", style="green")
            line.append(check["description"])
            console.print(line)
        else:
            line = Text("  ")
            line.append("\u2717 ", style="red")
            line.append(check["description"])
            line.append(
                f"  +{check['max']} pts", style="yellow"
            )
            console.print(line)
            if check.get("fix"):
                console.print(
                    f"    [dim]\u2192 {check['fix']}[/]"
                )

    console.print()

    # Suggestions
    if score < max_score:
        console.print(
            "  [dim]Fix the issues above and re-run:[/]"
            f"  [bold]skillctl lint {slug}[/]"
        )
        console.print()


# ══════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════


def _print_topic_header(fm: dict, topics: list[dict]) -> None:
    """Print topic title with position indicator."""
    title = fm.get("title", "").upper()
    order = fm.get("order", 0)
    total = len(topics)

    console.print()
    header = Text()
    header.append(f"  {title}", style="bold")
    pad = 50 - len(title)
    header.append(" " * max(pad, 2))
    header.append(f"{order} / {total}", style="dim")
    console.print(header)
    console.print()


def _print_nav_footer(fm: dict, topics: list[dict]) -> None:
    """Print navigation footer with next topic."""
    next_topic = fm.get("next")
    if next_topic:
        # Find next topic title
        next_title = next_topic
        for t in topics:
            if t["slug"] == next_topic:
                next_title = t["title"]
                break
        console.print(
            f"  [dim]Next:[/]  [bold]skillctl learn {next_topic}[/]"
            f"  [dim]({next_title})[/]"
        )
    else:
        console.print(
            "  [dim]Try:[/]  [bold]skillctl lint <skill>[/]"
            "  [dim](validate your skills)[/]"
        )
    console.print()


def _parse_points(text: str) -> list[str]:
    """Extract bullet points from markdown list."""
    points = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("- "):
            points.append(line[2:])
        elif line.startswith("* "):
            points.append(line[2:])
        elif re.match(r"^\d+\.\s", line):
            points.append(re.sub(r"^\d+\.\s", "", line))
    return points


def _extract_code_block(text: str) -> tuple[str, str]:
    """Extract first fenced code block. Returns (language, code)."""
    match = re.search(
        r"```(\w*)\n(.*?)```", text, re.DOTALL
    )
    if match:
        return match.group(1), match.group(2).strip()
    return "", ""


def _build_tree(text: str) -> Tree | None:
    """Build a Rich Tree from indented text lines."""
    lines = [l for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return None

    # First line is root
    root_text = lines[0].strip()
    root = Tree(
        f"[bold yellow]{root_text}[/]",
        guide_style="dim",
    )

    # Track indent levels → tree nodes
    stack: list[tuple[int, Tree]] = [(-1, root)]

    for line in lines[1:]:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Split name and description
        if "  " in stripped:
            parts = stripped.split("  ", 1)
            name = parts[0].strip()
            desc = parts[1].strip()
            label = f"[green]{name}[/]  [dim]{desc}[/]"
        else:
            name = stripped.strip()
            label = f"[green]{name}[/]"

        # Pop stack to find parent
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        parent = stack[-1][1]
        node = parent.add(label)
        stack.append((indent, node))

    return root


def _parse_markdown_table(text: str) -> Table | None:
    """Parse a simple markdown table into Rich Table."""
    lines = [
        l.strip()
        for l in text.strip().split("\n")
        if l.strip() and not l.strip().startswith("|---")
        and not re.match(r"^\|[\s\-|]+\|$", l.strip())
    ]

    if len(lines) < 2:
        return None

    # Parse header
    headers = [
        c.strip()
        for c in lines[0].strip("|").split("|")
    ]

    table = Table(
        show_header=True,
        box=box.SIMPLE,
        padding=(0, 1),
    )
    for h in headers:
        table.add_column(h, style="dim")

    # Parse rows
    for line in lines[1:]:
        cells = [
            c.strip() for c in line.strip("|").split("|")
        ]
        # Pad if needed
        while len(cells) < len(headers):
            cells.append("")
        table.add_row(*cells)

    return table


def _score_style(score: int) -> str:
    """Return style based on score value."""
    if score >= 80:
        return "bold green"
    if score >= 50:
        return "bold yellow"
    return "bold red"
