"""Content loader — parses learn topic markdown files."""

import re
from pathlib import Path
from typing import Optional

import yaml

CONTENT_DIR = Path(__file__).parent / "content"
EXAMPLES_DIR = CONTENT_DIR / "examples"


def load_topic(topic: str) -> dict:
    """Load a learn topic markdown file.

    Returns dict with:
      frontmatter: dict (title, subtitle, order, next)
      intro: str (text before first ## section)
      sections: list[dict] with keys:
        title: str (section header)
        label: str (subtitle after |)
        content: str (body text)
        subsections: dict[str, str] (### key → content)
    """
    path = CONTENT_DIR / f"{topic}.md"
    if not path.exists():
        return {"frontmatter": {}, "intro": "", "sections": []}

    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text)
    intro, sections = _parse_sections(body)

    return {
        "frontmatter": frontmatter,
        "intro": intro,
        "sections": sections,
    }


def load_example(name: str) -> Optional[dict]:
    """Load an example skill markdown file."""
    path = EXAMPLES_DIR / f"{name}.md"
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text)
    return {"frontmatter": frontmatter, "body": body, "raw": text}


def list_examples() -> list[dict]:
    """List available example skills."""
    examples = []
    if not EXAMPLES_DIR.exists():
        return examples
    for path in sorted(EXAMPLES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(text)
        examples.append({
            "slug": path.stem,
            "name": fm.get("name", path.stem),
            "description": fm.get("description", ""),
        })
    return examples


def list_topics() -> list[dict]:
    """List available learn topics in order."""
    topics = []
    for path in sorted(CONTENT_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(text)
        topics.append({
            "slug": path.stem,
            "title": fm.get("title", path.stem),
            "subtitle": fm.get("subtitle", ""),
            "order": fm.get("order", 99),
            "next": fm.get("next"),
        })
    topics.sort(key=lambda t: t["order"])
    return topics


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body."""
    if not text.startswith("---"):
        return {}, text.strip()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, parts[2].strip()


def _parse_sections(body: str) -> tuple[str, list[dict]]:
    """Parse body into intro text + sections.

    Correctly skips headers inside fenced code blocks.
    """
    lines = body.split("\n")
    intro_lines: list[str] = []
    sections: list[dict] = []
    current: Optional[dict] = None
    current_sub: Optional[str] = None
    in_code_block = False

    for line in lines:
        # Track fenced code blocks to avoid parsing headers inside them
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block

        if in_code_block:
            # Inside code block — treat as content, never as headers
            if current is not None:
                if current_sub is not None:
                    current["subsections"][current_sub] += line + "\n"
                else:
                    current["content"] += line + "\n"
            else:
                intro_lines.append(line)
            continue

        if line.startswith("## "):
            # Save previous section
            if current is not None:
                _finalize_section(current)
                sections.append(current)

            # Parse title and optional label: "## Name | label"
            raw_title = line[3:].strip()
            if "|" in raw_title:
                title, label = raw_title.split("|", 1)
                title = title.strip()
                label = label.strip()
            else:
                title = raw_title
                label = ""

            current = {
                "title": title,
                "label": label,
                "content": "",
                "subsections": {},
            }
            current_sub = None

        elif line.startswith("### "):
            sub_key = line[4:].strip().lower()
            if current is not None:
                current["subsections"][sub_key] = ""
                current_sub = sub_key

        elif current is not None:
            if current_sub is not None:
                current["subsections"][current_sub] += line + "\n"
            else:
                current["content"] += line + "\n"

        else:
            intro_lines.append(line)

    # Save last section
    if current is not None:
        _finalize_section(current)
        sections.append(current)

    return "\n".join(intro_lines).strip(), sections


def _finalize_section(section: dict) -> None:
    """Clean up section content."""
    section["content"] = section["content"].strip()
    for key in section["subsections"]:
        section["subsections"][key] = section["subsections"][key].strip()
