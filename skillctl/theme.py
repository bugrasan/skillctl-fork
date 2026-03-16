"""skillctl design system — semantic theme and ASCII art."""

from rich.theme import Theme

SKILLCTL_THEME = Theme(
    {
        # Semantic styles
        "intent": "green",  # success, installed, skill names, checkmarks
        "source": "cyan",  # origin info, source column, flags
        "machine": "blue",  # repo names, table headers, URLs
        "identity": "magenta",  # tags, dry-run, schema, preview
        "value": "yellow",  # stars, paths, config values, strings
        "danger": "red",  # errors, destructive actions
        "chrome": "dim",  # metadata, hints, timestamps, connective tissue
        # Dot language
        "dot.installed": "green",
        "dot.available": "dim",
        # Component styles
        "header.name": "bold blue",
        "header.desc": "dim",
        "label": "dim",
        "rule": "dim",
        "warning": "yellow",
    }
)

# ── ASCII Art ──
# "Calvin S" inspired — compact 3-line box-drawing wordmark
# "skill" in white/bold, "ctl" in green/bold

LOGO_SKILL_LINES = [
    "╔═╗╦╔═╦╦  ╦  ",
    "╚═╗╠╩╗║║  ║  ",
    "╚═╝╩ ╩╩╩═╝╩═╝",
]

LOGO_CTL_LINES = [
    "╔═╗╔╦╗╦  ",
    "║   ║ ║  ",
    "╚═╝ ╩ ╩═╝",
]


def get_logo_lines() -> list[tuple[str, str]]:
    """Return logo as list of (skill_part, ctl_part) tuples per line."""
    return list(zip(LOGO_SKILL_LINES, LOGO_CTL_LINES))
