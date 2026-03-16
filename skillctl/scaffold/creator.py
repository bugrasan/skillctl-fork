"""Skill scaffolding — create new skills from templates."""

from pathlib import Path

from jinja2 import Environment, PackageLoader

from .. import manifest
from ..config import Config, load_config


def create_skill(
    slug: str,
    name: str,
    description: str = "",
    tags: list[str] | None = None,
    author: str = "",
    config: Config | None = None,
) -> dict:
    """Create a new skill directory with SKILL.md.

    Returns dict with created paths.
    """
    if config is None:
        config = load_config()

    tags = tags or []
    skill_dir = config.skills_path / slug

    if skill_dir.exists():
        raise FileExistsError(f"Skill directory already exists: {skill_dir}")

    skill_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=PackageLoader("skillctl", "scaffold/templates"),
        keep_trailing_newline=True,
    )
    template = env.get_template("SKILL.md.j2")

    content = template.render(
        name=name,
        description=description,
        tags=tags,
        author=author,
    )

    skill_md_path = skill_dir / "SKILL.md"
    skill_md_path.write_text(content, encoding="utf-8")

    manifest.add_skill(
        slug,
        {
            "name": name,
            "slug": slug,
            "source": "local",
            "description": description,
            "tags": tags,
            "author": author,
            "path": str(skill_dir),
        },
    )

    return {
        "status": "created",
        "name": name,
        "slug": slug,
        "path": str(skill_dir),
        "skill_md": str(skill_md_path),
    }
