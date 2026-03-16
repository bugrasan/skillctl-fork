"""Tests for YAML frontmatter parser."""

from pathlib import Path

from skillctl.utils.frontmatter import parse_frontmatter


def test_parse_valid_frontmatter(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text(
        "---\n"
        "name: My Skill\n"
        "description: Does stuff\n"
        "tags: [a, b]\n"
        "---\n"
        "\n"
        "# Body\n"
    )
    meta, body = parse_frontmatter(md)
    assert meta["name"] == "My Skill"
    assert meta["description"] == "Does stuff"
    assert meta["tags"] == ["a", "b"]
    assert "# Body" in body


def test_parse_no_frontmatter(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("# Just a heading\n\nSome text.\n")
    meta, body = parse_frontmatter(md)
    assert meta == {}
    assert "# Just a heading" in body


def test_parse_empty_frontmatter(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("---\n---\n\n# Body\n")
    meta, body = parse_frontmatter(md)
    assert meta == {}
    assert "# Body" in body


def test_parse_invalid_yaml(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("---\n: invalid: yaml: [[\n---\n\n# Body\n")
    meta, body = parse_frontmatter(md)
    assert meta == {}
    assert "# Body" in body
