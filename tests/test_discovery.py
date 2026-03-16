"""Tests for local skill discovery."""

from pathlib import Path

from skillctl.config import Config
from skillctl.discovery.local import scan_local_skills, search_local


def _make_skill(skills_dir: Path, name: str, description: str = "", tags: str = "") -> Path:
    """Create a skill directory with SKILL.md."""
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    tag_line = f"tags: [{tags}]" if tags else "tags: []"
    (skill_dir / "SKILL.md").write_text(
        f"---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"{tag_line}\n"
        f"---\n"
        f"\n"
        f"# {name}\n"
    )
    return skill_dir


def test_scan_finds_skills(skill_env):
    _make_skill(skill_env["skills_dir"], "pdf-tool", "Process PDFs")
    _make_skill(skill_env["skills_dir"], "csv-tool", "Process CSVs")

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    results = scan_local_skills(config)
    assert len(results) == 2
    slugs = {r["slug"] for r in results}
    assert "pdf-tool" in slugs
    assert "csv-tool" in slugs


def test_scan_ignores_dirs_without_skill_md(skill_env):
    (skill_env["skills_dir"] / "no-skill").mkdir()
    _make_skill(skill_env["skills_dir"], "has-skill", "Has SKILL.md")

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    results = scan_local_skills(config)
    assert len(results) == 1
    assert results[0]["slug"] == "has-skill"


def test_scan_includes_scan_paths(skill_env):
    extra = skill_env["tmp_path"] / "extra-skills"
    extra.mkdir()
    _make_skill(extra, "extra-skill", "From extra path")

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
        scan_paths=[str(extra)],
    )
    results = scan_local_skills(config)
    assert any(r["slug"] == "extra-skill" for r in results)


def test_search_filters_by_query(skill_env):
    _make_skill(skill_env["skills_dir"], "pdf-tool", "Process PDFs", "pdf")
    _make_skill(skill_env["skills_dir"], "csv-tool", "Process CSVs", "csv")

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    results = search_local(config, "pdf")
    assert len(results) == 1
    assert results[0]["slug"] == "pdf-tool"


def test_search_matches_tags(skill_env):
    _make_skill(skill_env["skills_dir"], "analyzer", "Data analysis", "data, ml")

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    results = search_local(config, "ml")
    assert len(results) == 1


def test_search_no_results(skill_env):
    _make_skill(skill_env["skills_dir"], "pdf-tool", "Process PDFs")

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    results = search_local(config, "nonexistent-query")
    assert len(results) == 0


def test_scan_parses_metadata(skill_env):
    _make_skill(skill_env["skills_dir"], "my-skill", "My description", "tag1, tag2")

    config = Config(
        skills_dir=str(skill_env["skills_dir"]),
        repos_dir=str(skill_env["repos_dir"]),
    )
    results = scan_local_skills(config)
    assert len(results) == 1
    r = results[0]
    assert r["name"] == "my-skill"
    assert r["description"] == "My description"
    assert r["source"] == "local"
    assert r["installed"] is True
