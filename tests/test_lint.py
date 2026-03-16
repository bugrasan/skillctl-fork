"""Tests for skillctl lint module."""

import json
from pathlib import Path

from typer.testing import CliRunner

from skillctl.cli import app
from skillctl.lint import lint_skill, lint_result_to_dict

runner = CliRunner()


# ── Core lint tests ──


class TestLintSkill:
    def test_lint_perfect_skill(self, tmp_path):
        """A well-structured skill should score 100."""
        skill_dir = tmp_path / "good-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""\
---
name: good-skill
description: A well-written skill for testing purposes
tags: [testing, example]
author: test
version: 1.0.0
---

# Good Skill

## When to Use This Skill
Use when testing the lint system.

## Core Principles
- Always write tests
- Never skip validation

## Step-by-Step Process
1. Write the skill
2. Lint it
3. Fix issues

## Common Mistakes to Avoid
- Do NOT skip the trigger section
- Do NOT use vague language

## Examples
```python
def hello():
    return "world"
```
""")
        result = lint_skill(skill_dir)
        assert result.score == result.max_score
        assert result.score == 100
        assert all(c.passed for c in result.checks)

    def test_lint_minimal_skill(self, tmp_path):
        """A minimal skill should score low."""
        skill_dir = tmp_path / "minimal"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""\
---
name: minimal
---

# Minimal

Some content.
""")
        result = lint_skill(skill_dir)
        assert result.score < 50
        assert not all(c.passed for c in result.checks)

    def test_lint_missing_file(self, tmp_path):
        """Missing SKILL.md should score 0."""
        skill_dir = tmp_path / "empty"
        skill_dir.mkdir()
        result = lint_skill(skill_dir)
        assert result.score == 0

    def test_lint_file_directly(self, tmp_path):
        """Can lint a .md file directly."""
        md = tmp_path / "test.md"
        md.write_text("""\
---
name: test
description: Test skill for linting validation
tags: [test]
---

## When to Use
Always use this.

## Core Principles
- Always test
- Never skip

## Common Mistakes to Avoid
- Don't forget tests

## Examples
```python
x = 1
```
""")
        result = lint_skill(md)
        assert result.score > 50

    def test_lint_detects_placeholders(self, tmp_path):
        """Placeholder comments should fail the check."""
        skill_dir = tmp_path / "placeholder"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""\
---
name: placeholder
description: This skill has placeholder content inside
tags: [test]
---

## When to Use
Always.

## Core Principles
- Always do this
- Never do that
- Must follow rules

<!-- TODO: fill in more content -->

## Common Mistakes to Avoid
- Don't use placeholders

## Examples
```python
x = 1
```
""")
        result = lint_skill(skill_dir)
        placeholder_check = next(
            c for c in result.checks if c.name == "no_placeholders"
        )
        assert not placeholder_check.passed

    def test_lint_detects_vague_language(self, tmp_path):
        """Vague language should reduce the score."""
        skill_dir = tmp_path / "vague"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""\
---
name: vague
description: This skill uses vague language throughout
tags: [test]
---

## When to Use
Consider using this skill when appropriate.

## Core Principles
- You might want to consider doing this
- It can be helpful to follow these guidelines
- Some teams prefer this approach
- You may want to think about it
- It's generally a good idea

## Common Mistakes to Avoid
- You could consider avoiding this

## Examples
```python
x = 1
```
""")
        result = lint_skill(skill_dir)
        imperative_check = next(
            c for c in result.checks if c.name == "uses_imperative"
        )
        assert not imperative_check.passed

    def test_lint_result_to_dict(self, tmp_path):
        """Result dict should be JSON-serializable."""
        skill_dir = tmp_path / "dicttest"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""\
---
name: dicttest
description: Testing dict conversion works properly
tags: [test]
---
# Test
""")
        result = lint_skill(skill_dir)
        d = lint_result_to_dict(result)
        assert isinstance(d, dict)
        assert "score" in d
        assert "checks" in d
        # Should be JSON-serializable
        json.dumps(d)


# ── CLI tests ──


class TestLintCLI:
    def test_lint_example_skill(self):
        """Lint a bundled example — should score 100."""
        result = runner.invoke(app, ["lint", "sql-standards"])
        assert result.exit_code == 0
        assert "100/100" in result.output

    def test_lint_example_json(self):
        result = runner.invoke(
            app, ["lint", "sql-standards", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["score"] == 100
        assert "next_actions" in data

    def test_lint_not_found(self):
        result = runner.invoke(app, ["lint", "nonexistent-skill"])
        assert result.exit_code == 2
