"""Tests for skill scaffolding."""

from pathlib import Path

from skillctl import manifest
from skillctl.config import Config
from skillctl.scaffold.creator import create_skill
from skillctl.utils.frontmatter import parse_frontmatter


def test_create_skill_basic(skill_env):
    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    result = create_skill(
        slug="my-skill",
        name="My Skill",
        description="Test description",
        tags=["test", "demo"],
        author="tester",
        config=config,
    )

    assert result["status"] == "created"
    assert result["slug"] == "my-skill"
    assert Path(result["path"]).exists()
    assert Path(result["skill_md"]).exists()

    # Verify SKILL.md content
    meta, body = parse_frontmatter(Path(result["skill_md"]))
    assert meta["name"] == "My Skill"
    assert meta["description"] == "Test description"
    assert meta["tags"] == ["test", "demo"]
    assert meta["author"] == "tester"


def test_create_registers_in_manifest(skill_env):
    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    create_skill(
        slug="registered-skill",
        name="Registered",
        config=config,
    )

    assert manifest.is_installed("registered-skill")
    skill = manifest.get_skill("registered-skill")
    assert skill["source"] == "local"
    assert skill["name"] == "Registered"


def test_create_duplicate_raises(skill_env):
    import pytest

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    create_skill(slug="dup", name="Dup", config=config)

    with pytest.raises(FileExistsError):
        create_skill(slug="dup", name="Dup Again", config=config)


def test_create_with_empty_tags(skill_env):
    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    result = create_skill(
        slug="no-tags",
        name="No Tags",
        config=config,
    )
    meta, _ = parse_frontmatter(Path(result["skill_md"]))
    assert meta["tags"] == []


def test_create_skill_directory_structure(skill_env):
    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    result = create_skill(slug="struct", name="Struct", config=config)

    skill_dir = Path(result["path"])
    assert skill_dir.is_dir()
    assert (skill_dir / "SKILL.md").is_file()
