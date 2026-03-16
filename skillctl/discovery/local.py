"""Local filesystem skill discovery."""

from pathlib import Path

from ..config import Config
from ..utils.frontmatter import parse_frontmatter


def scan_local_skills(config: Config) -> list[dict]:
    """Scan configured directories for skills with SKILL.md."""
    results = []
    seen_paths: set[str] = set()

    dirs_to_scan = [config.skills_path] + config.get_scan_paths()

    for scan_dir in dirs_to_scan:
        if not scan_dir.exists():
            continue

        # Check immediate subdirectories for SKILL.md (don't recurse deeply)
        for child in sorted(scan_dir.iterdir()):
            if not child.is_dir():
                continue

            skill_md = child / "SKILL.md"
            if not skill_md.exists():
                continue

            real_path = str(child.resolve())
            if real_path in seen_paths:
                continue
            seen_paths.add(real_path)

            metadata, _body = parse_frontmatter(skill_md)
            slug = child.name

            results.append(
                {
                    "name": metadata.get("name") or slug,
                    "slug": slug,
                    "source": "local",
                    "description": metadata.get("description") or "",
                    "tags": metadata.get("tags") or [],
                    "author": metadata.get("author") or "",
                    "path": str(child),
                    "installed": True,
                }
            )

    return results


def search_local(config: Config, query: str) -> list[dict]:
    """Search local skills matching a query."""
    all_skills = scan_local_skills(config)
    query_lower = query.lower()

    results = []
    for skill in all_skills:
        searchable = " ".join(
            [
                skill.get("name", "") or "",
                skill.get("slug", "") or "",
                skill.get("description", "") or "",
                " ".join(t for t in (skill.get("tags") or []) if t),
            ]
        ).lower()

        if query_lower in searchable:
            results.append(skill)

    return results
