"""Shared fixtures for skillctl tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


@pytest.fixture
def skill_env(tmp_path):
    """Set up isolated skillctl environment with temp directories."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    repos_dir = tmp_path / "repos"
    repos_dir.mkdir()
    skillctl_dir = tmp_path / "skillctl_home"
    skillctl_dir.mkdir()
    manifest_path = skillctl_dir / "manifest.json"
    config_path = skillctl_dir / "config.yaml"

    # Write a config file so load_config reads temp paths
    with open(config_path, "w") as f:
        yaml.dump(
            {
                "skills_dir": str(skills_dir),
                "repos_dir": str(repos_dir),
            },
            f,
        )

    # Patch all the paths
    patches = [
        patch("skillctl.config.SKILLCTL_DIR", skillctl_dir),
        patch("skillctl.config.CONFIG_PATH", config_path),
        patch("skillctl.config.DEFAULT_SKILLS_DIR", skills_dir),
        patch("skillctl.config.DEFAULT_REPOS_DIR", repos_dir),
        patch("skillctl.manifest.SKILLCTL_DIR", skillctl_dir),
        patch("skillctl.manifest.MANIFEST_PATH", manifest_path),
    ]
    for p in patches:
        p.start()

    yield {
        "tmp_path": tmp_path,
        "skills_dir": skills_dir,
        "repos_dir": repos_dir,
        "skillctl_dir": skillctl_dir,
        "manifest_path": manifest_path,
        "config_path": config_path,
    }

    for p in patches:
        p.stop()


@pytest.fixture
def sample_skill_md(tmp_path):
    """Create a sample SKILL.md file."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\n"
        "name: Test Skill\n"
        "description: A test skill for testing\n"
        "tags: [test, demo]\n"
        "author: tester\n"
        "version: 1.0.0\n"
        "---\n"
        "\n"
        "# Test Skill\n"
        "\n"
        "This is a test skill.\n"
    )
    return skill_dir
