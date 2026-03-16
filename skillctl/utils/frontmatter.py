"""Parse YAML frontmatter from SKILL.md files."""

from pathlib import Path

import yaml


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter and body from a markdown file.

    Returns (metadata_dict, body_string).
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        metadata = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        metadata = {}

    body = parts[2].strip()
    return metadata, body
