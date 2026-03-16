"""Pixel art boot animation for the skillctl welcome screen.

A pixel art gem materializes from particles, then a "forge wave"
sweeps left-to-right across the logo, transmuting noise blocks
into the real characters. Sparkles and embers trail the wavefront.

All frames are center-aligned to match the welcome screen layout.

Skipped automatically when stdout is not a TTY (pipes, CI, JSON mode).
"""

import random
import sys
import time

from rich.align import Align
from rich.console import Group
from rich.text import Text

from .theme import LOGO_CTL_LINES, LOGO_SKILL_LINES

# ── Tunables ──

NOISE_CHARS = "░▒▓█▀▄╔╗╚╝═║╦╩╠╣"
SPARK_CHARS = ["✦", "✧", "·", "*"]

# ── Pixel art gem frames ──

_GEM = [
    # 0: Dust
    (
        [
            "          ·    ✧    ·",
            "       ✦       ·    ✦",
            "          ✧    ✦    ·",
        ],
        "dim",
    ),
    # 1: Noise outline
    (
        [
            "            ░░░░",
            "          ░░░░░░░░",
            "          ░░░░░░░░",
            "            ░░░░",
        ],
        "dim green",
    ),
    # 2: Taking shape
    (
        [
            "            ▄▒▒▄",
            "          ▄▒▒▒▒▒▒▄",
            "          ▀▒▒▒▒▒▒▀",
            "            ▀▒▒▀",
        ],
        "green",
    ),
    # 3: Crystal formed
    (
        [
            "            ▄██▄",
            "          ▄█▓▒▒▓█▄",
            "          ▀█▓▒▒▓█▀",
            "            ▀██▀",
        ],
        "bold green",
    ),
    # 4: Glowing + sparkles
    (
        [
            "       ✦    ▄██▄    ✦",
            "     ✧    ▄█▓▒▒▓█▄    ✧",
            "     ✧    ▀█▓▒▒▓█▀    ✧",
            "       ✦    ▀██▀    ✦",
        ],
        "bold green",
    ),
    # 5: Pulsing bright
    (
        [
            "     ·  ✦  ▄████▄  ✦  ·",
            "   ✧   ▄██████████▄   ✧",
            "   ✧   ▀██████████▀   ✧",
            "     ·  ✦  ▀████▀  ✦  ·",
        ],
        "bold bright_green",
    ),
]


# ── Helpers ──


def _logo_pairs() -> list[tuple[str, str]]:
    return list(zip(LOGO_SKILL_LINES, LOGO_CTL_LINES))


def _full_logo_width() -> int:
    return len(LOGO_SKILL_LINES[0]) + 1 + len(LOGO_CTL_LINES[0])


def _center(renderable) -> Align:
    return Align.center(renderable)


# ── Frame builders ──


def _frame_gem_noise(gem_idx: int) -> Align:
    """Gem materializing + full noise logo underneath."""
    parts: list = []

    lines, style = _GEM[min(gem_idx, len(_GEM) - 1)]
    for s in lines:
        parts.append(Text(s, style=style))

    parts.append(Text())

    noise_styles = ["dim green", "green", "dim cyan", "dim"]
    for skill_part, ctl_part in _logo_pairs():
        full = skill_part + " " + ctl_part
        line = Text()
        for ch in full:
            if ch == " ":
                line.append(" ")
            else:
                line.append(
                    random.choice(NOISE_CHARS),
                    style=random.choice(noise_styles),
                )
        parts.append(line)

    return _center(Group(*parts))


def _frame_forge(reveal_col: int) -> Align:
    """Forge wave at a specific column. Gem at full glow."""
    parts: list = []
    width = _full_logo_width()
    skill_len = len(LOGO_SKILL_LINES[0])

    lines, style = _GEM[5]
    for s in lines:
        parts.append(Text(s, style=style))

    # Spark cursor line
    spark = Text()
    for i in range(width):
        if i == reveal_col:
            spark.append("✦", style="bold yellow")
        elif abs(i - reveal_col) == 1:
            spark.append("·", style="yellow")
        elif reveal_col - 5 < i < reveal_col - 1 and random.random() < 0.35:
            spark.append(random.choice(SPARK_CHARS), style="dim yellow")
        else:
            spark.append(" ")
    parts.append(spark)

    for skill_part, ctl_part in _logo_pairs():
        full = skill_part + " " + ctl_part
        line = Text()
        for i, ch in enumerate(full):
            if ch == " ":
                line.append(" ")
            elif i < reveal_col - 2:
                s = "bold" if i < skill_len else "bold green"
                line.append(ch, style=s)
            elif i < reveal_col:
                line.append(ch, style="bold bright_white")
            elif i == reveal_col:
                line.append(ch, style="bold yellow")
            else:
                line.append(
                    random.choice(NOISE_CHARS),
                    style="dim" if random.random() < 0.5 else "dim green",
                )
        parts.append(line)

    return _center(Group(*parts))


def _frame_burst() -> Align:
    """Sparkle burst — logo flashes bright, particles fly."""
    parts: list = []
    width = _full_logo_width()

    top = Text()
    for _ in range(width):
        if random.random() < 0.3:
            top.append(
                random.choice(SPARK_CHARS),
                style=random.choice([
                    "bold yellow", "yellow", "bold green",
                    "bright_green", "dim yellow",
                ]),
            )
        else:
            top.append(" ")
    parts.append(top)
    parts.append(Text())

    for skill_part, ctl_part in _logo_pairs():
        line = Text()
        line.append(skill_part, style="bold bright_white")
        line.append(" ")
        line.append(ctl_part, style="bold bright_green")
        parts.append(line)

    parts.append(Text())
    bot = Text()
    for _ in range(width):
        if random.random() < 0.2:
            bot.append(
                random.choice(SPARK_CHARS),
                style=random.choice(["dim yellow", "dim green", "dim"]),
            )
        else:
            bot.append(" ")
    parts.append(bot)

    return _center(Group(*parts))


def _frame_settle() -> Align:
    """Settling — logo in final colors with gradient bar."""
    parts: list = []
    parts.append(Text())

    for skill_part, ctl_part in _logo_pairs():
        line = Text()
        line.append(skill_part, style="bold")
        line.append(" ")
        line.append(ctl_part, style="bold green")
        parts.append(line)

    parts.append(Text())
    bar = Text()
    bar_str = "░▒▓████████████████████████████████████▓▒░"
    mid = len(bar_str) // 2
    for i, ch in enumerate(bar_str):
        dist = abs(i - mid)
        ratio = 1 - (dist / max(mid, 1))
        if ratio > 0.7:
            bar.append(ch, style="bold green")
        elif ratio > 0.4:
            bar.append(ch, style="green")
        elif ratio > 0.2:
            bar.append(ch, style="dim green")
        else:
            bar.append(ch, style="bright_black")
    parts.append(bar)

    return _center(Group(*parts))


def _frame_final() -> Align:
    """Clean final logo — no animation artifacts."""
    parts: list = []
    parts.append(Text())

    for skill_part, ctl_part in _logo_pairs():
        line = Text()
        line.append(skill_part, style="bold")
        line.append(" ")
        line.append(ctl_part, style="bold green")
        parts.append(line)

    return _center(Group(*parts))


# ── Main ──


def play_boot_animation(console) -> bool:
    """Play the pixel art forge animation.

    Returns True if animation played, False if skipped.
    The final logo frame stays on screen (centered).
    """
    if not sys.stdout.isatty():
        return False

    try:
        from rich.live import Live
    except ImportError:
        return False

    width = _full_logo_width()

    frames: list[tuple] = []

    # Phase 1 — Gem materializes (4 frames, ~400ms)
    for i in range(4):
        frames.append((_frame_gem_noise(i), 0.10))

    # Phase 2 — Gem full glow (2 frames, ~200ms)
    frames.append((_frame_gem_noise(4), 0.10))
    frames.append((_frame_gem_noise(5), 0.10))

    # Phase 3 — Forge wave (8 frames, ~500ms)
    step = max(1, width // 8)
    for col in range(0, width + step, step):
        frames.append((_frame_forge(min(col, width)), 0.06))

    # Phase 4 — Sparkle burst (2 frames, ~250ms)
    frames.append((_frame_burst(), 0.15))
    frames.append((_frame_burst(), 0.10))

    # Phase 5 — Settle with gradient bar (1 frame, 200ms)
    frames.append((_frame_settle(), 0.20))

    # Phase 6 — Clean final logo (stays on screen)
    frames.append((_frame_final(), 0.01))

    try:
        with Live(
            console=console, transient=False, refresh_per_second=30
        ) as live:
            for frame, delay in frames:
                live.update(frame)
                time.sleep(delay)
    except Exception:
        return False

    return True
