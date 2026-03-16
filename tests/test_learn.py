"""Tests for skillctl learn module."""

import json

from typer.testing import CliRunner

from skillctl.cli import app
from skillctl.learn.loader import (
    list_examples,
    list_topics,
    load_example,
    load_topic,
)

runner = CliRunner()


# ── Loader tests ──


class TestLoader:
    def test_list_topics_returns_ordered(self):
        topics = list_topics()
        assert len(topics) >= 3
        # Should be sorted by order
        orders = [t["order"] for t in topics]
        assert orders == sorted(orders)

    def test_list_topics_have_required_fields(self):
        for topic in list_topics():
            assert "slug" in topic
            assert "title" in topic
            assert "order" in topic

    def test_load_anatomy(self):
        data = load_topic("anatomy")
        assert data["frontmatter"]["title"] == "Anatomy of a Skill"
        assert len(data["sections"]) == 5
        assert data["intro"]

    def test_load_write(self):
        data = load_topic("write")
        assert data["frontmatter"]["title"] == "Writing for AI Comprehension"
        assert len(data["sections"]) >= 4

    def test_load_organize(self):
        data = load_topic("organize")
        assert data["frontmatter"]["title"] == "Organizing Your Skills Library"

    def test_load_nonexistent(self):
        data = load_topic("nonexistent")
        assert data["sections"] == []
        assert data["intro"] == ""

    def test_sections_have_structure(self):
        data = load_topic("anatomy")
        for section in data["sections"]:
            assert "title" in section
            assert "label" in section
            assert "content" in section
            assert "subsections" in section

    def test_code_blocks_not_parsed_as_headers(self):
        """Code blocks containing ## should not create sections."""
        data = load_topic("anatomy")
        # anatomy.md has code blocks with ## headers inside
        # Should have exactly 5 sections, not more
        assert len(data["sections"]) == 5

    def test_list_examples(self):
        examples = list_examples()
        assert len(examples) >= 2
        slugs = [e["slug"] for e in examples]
        assert "sql-standards" in slugs
        assert "api-patterns" in slugs

    def test_load_example(self):
        ex = load_example("sql-standards")
        assert ex is not None
        assert ex["frontmatter"]["name"] == "sql-standards"
        assert "body" in ex
        assert "raw" in ex

    def test_load_example_not_found(self):
        assert load_example("nonexistent") is None


# ── CLI tests ──


class TestLearnCLI:
    def test_learn_index(self):
        result = runner.invoke(app, ["learn"])
        assert result.exit_code == 0
        assert "LEARN" in result.output
        assert "anatomy" in result.output

    def test_learn_index_json(self):
        result = runner.invoke(app, ["learn", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "topics" in data
        assert "next_actions" in data
        assert len(data["topics"]) >= 3

    def test_learn_anatomy(self):
        result = runner.invoke(app, ["learn", "anatomy"])
        assert result.exit_code == 0
        assert "ANATOMY" in result.output
        assert "FRONTMATTER" in result.output

    def test_learn_anatomy_json(self):
        result = runner.invoke(app, ["learn", "anatomy", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["topic"] == "anatomy"
        assert len(data["layers"]) == 5
        assert "next_actions" in data

    def test_learn_write(self):
        result = runner.invoke(app, ["learn", "write"])
        assert result.exit_code == 0
        assert "RULE 1" in result.output

    def test_learn_write_json(self):
        result = runner.invoke(app, ["learn", "write", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["topic"] == "write"
        assert "rules" in data

    def test_learn_organize(self):
        result = runner.invoke(app, ["learn", "organize"])
        assert result.exit_code == 0
        assert ".claude/skills/" in result.output

    def test_learn_organize_json(self):
        result = runner.invoke(app, ["learn", "organize", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["topic"] == "organize"

    def test_learn_examples_list(self):
        result = runner.invoke(app, ["learn", "examples"])
        assert result.exit_code == 0
        assert "sql-standards" in result.output

    def test_learn_examples_detail(self):
        result = runner.invoke(
            app, ["learn", "examples", "sql-standards"]
        )
        assert result.exit_code == 0
        assert "SQL" in result.output

    def test_learn_examples_json(self):
        result = runner.invoke(app, ["learn", "examples", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "examples" in data

    def test_learn_examples_detail_json(self):
        result = runner.invoke(
            app, ["learn", "examples", "sql-standards", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["example"] == "sql-standards"
        assert "next_actions" in data

    def test_learn_examples_not_found(self):
        result = runner.invoke(
            app, ["learn", "examples", "nonexistent"]
        )
        assert result.exit_code == 2
