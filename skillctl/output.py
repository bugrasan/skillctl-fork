"""Dual output: Rich tables for humans, JSON for agents."""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from rich.console import Console

from .theme import SKILLCTL_THEME

console = Console(stderr=False, theme=SKILLCTL_THEME)
err_console = Console(stderr=True, theme=SKILLCTL_THEME)


def print_json(
    data: Any, next_actions: Optional[list[str]] = None
) -> None:
    """Print JSON to stdout."""
    if isinstance(data, dict) and next_actions:
        data = {**data, "next_actions": next_actions}
    elif isinstance(data, list) and next_actions:
        data = {"results": data, "next_actions": next_actions}
    print(json.dumps(data, indent=2, default=str))


def print_error(
    message: str,
    json_output: bool = False,
    code: int = 1,
    hint: Optional[str] = None,
    valid_flags: Optional[list[str]] = None,
    expected_pattern: Optional[str] = None,
) -> None:
    """Print error to stderr (human) or structured JSON (agent)."""
    if json_output:
        error: dict[str, Any] = {
            "status": "error",
            "code": code,
            "message": message,
        }
        if valid_flags:
            error["valid_flags"] = valid_flags
        if expected_pattern:
            error["expected_pattern"] = expected_pattern
        print(json.dumps(error, indent=2))
    else:
        err_console.print(f"  [danger]✗ {message}[/]")
        if hint:
            err_console.print(f"  [chrome]{hint}[/]")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"  [intent]✓[/] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"  [machine]ℹ[/] {message}")


def print_warning(message: str) -> None:
    """Print a warning to stderr."""
    err_console.print(f"  [warning]⚠ {message}[/]")


def print_dim(message: str) -> None:
    """Print dim/secondary text."""
    console.print(f"  [chrome]{message}[/]")


def relative_time(iso_str: str) -> str:
    """Convert ISO timestamp to human-readable relative time."""
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 30:
            return f"{days}d ago"
        months = days // 30
        if months < 12:
            return f"{months}mo ago"
        years = days // 365
        return f"{years}y ago"
    except (ValueError, TypeError):
        return ""


def filter_fields(data: Any, fields: Optional[str]) -> Any:
    """Apply field mask to output data."""
    if not fields:
        return data

    field_list = [f.strip() for f in fields.split(",")]

    if isinstance(data, list):
        return [
            {k: v for k, v in item.items() if k in field_list}
            for item in data
            if isinstance(item, dict)
        ]
    elif isinstance(data, dict):
        return {k: v for k, v in data.items() if k in field_list}
    return data
