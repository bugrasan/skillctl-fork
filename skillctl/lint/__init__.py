"""skillctl lint — score and validate skill quality.

Rule-based checks with optional LLM deepening.
Designed for the create-lint-fix-lint agent loop.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..output import print_error, print_json
from ..learn.renderer import render_lint_result


# ── Rule definitions ──


@dataclass
class CheckResult:
    name: str
    description: str
    passed: bool
    points: int
    max: int
    fix: str = ""


@dataclass
class LintResult:
    slug: str
    path: str
    score: int
    max_score: int
    checks: list[CheckResult] = field(default_factory=list)


# ── Frontmatter parser ──


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split frontmatter from body."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, parts[2].strip()


# ── Individual rule checks ──

# Patterns for section detection (case-insensitive)
_TRIGGER_PATTERNS = re.compile(
    r"^##\s+(when\s+to\s+use|triggers?|activation|applies?\s+when)",
    re.IGNORECASE | re.MULTILINE,
)
_PRINCIPLE_PATTERNS = re.compile(
    r"^##\s+(core\s+principles?|rules?|standards?|guidelines?|requirements?)",
    re.IGNORECASE | re.MULTILINE,
)
_ANTIPATTERN_PATTERNS = re.compile(
    r"^##\s+(common\s+mistakes?|mistakes?\s+to\s+avoid|"
    r"anti.?patterns?|avoid|don.?t|pitfalls?)",
    re.IGNORECASE | re.MULTILINE,
)
_STEP_PATTERNS = re.compile(
    r"^##\s+(step.?by.?step|process|workflow|how\s+to|procedure|instructions?)",
    re.IGNORECASE | re.MULTILINE,
)
_EXAMPLE_PATTERNS = re.compile(
    r"^##\s+examples?",
    re.IGNORECASE | re.MULTILINE,
)

# Imperative markers
_IMPERATIVE_WORDS = re.compile(
    r"\b(always|never|must|do not|don't|shall|required?)\b",
    re.IGNORECASE,
)
_VAGUE_WORDS = re.compile(
    r"\b(consider|might|could|you may want|it can be helpful|"
    r"you might want|it's? generally|some teams?)\b",
    re.IGNORECASE,
)

# Placeholder patterns
_PLACEHOLDER_PATTERNS = re.compile(
    r"(<!--\s*(add|todo|fixme|placeholder|insert|fill)|"
    r"\bTODO\b|\bFIXME\b|\bXXX\b)",
    re.IGNORECASE,
)


def _check_frontmatter(fm: dict) -> CheckResult:
    """Check frontmatter completeness."""
    has_name = bool(fm.get("name"))
    has_desc = bool(fm.get("description"))
    has_tags = bool(fm.get("tags"))

    passed = has_name and has_desc and has_tags
    missing = []
    if not has_name:
        missing.append("name")
    if not has_desc:
        missing.append("description")
    if not has_tags:
        missing.append("tags")

    fix = ""
    if missing:
        fix = f"Add missing frontmatter fields: {', '.join(missing)}"

    return CheckResult(
        name="frontmatter_complete",
        description="Has name, description, and tags in frontmatter",
        passed=passed,
        points=10 if passed else 0,
        max=10,
        fix=fix,
    )


def _check_description_quality(fm: dict) -> CheckResult:
    """Check description is meaningful."""
    desc = fm.get("description", "")
    passed = len(desc) >= 20

    return CheckResult(
        name="description_quality",
        description="Description is meaningful (20+ chars)",
        passed=passed,
        points=5 if passed else 0,
        max=5,
        fix="Write a description that explains what this skill teaches"
        if not passed
        else "",
    )


def _check_triggers(body: str) -> CheckResult:
    """Check for trigger/when-to-use section."""
    passed = bool(_TRIGGER_PATTERNS.search(body))

    return CheckResult(
        name="has_triggers",
        description="Has 'When to Use' trigger section",
        passed=passed,
        points=20 if passed else 0,
        max=20,
        fix="Add a '## When to Use This Skill' section"
        if not passed
        else "",
    )


def _check_principles(body: str) -> CheckResult:
    """Check for core principles/rules section."""
    passed = bool(_PRINCIPLE_PATTERNS.search(body))

    return CheckResult(
        name="has_principles",
        description="Has core principles or rules section",
        passed=passed,
        points=15 if passed else 0,
        max=15,
        fix="Add a '## Core Principles' section with imperative rules"
        if not passed
        else "",
    )


def _check_examples(body: str) -> CheckResult:
    """Check for code examples."""
    code_blocks = re.findall(r"```\w*\n", body)
    has_example_section = bool(_EXAMPLE_PATTERNS.search(body))
    passed = len(code_blocks) >= 1 and has_example_section

    if not code_blocks:
        fix = "Add code examples in fenced code blocks (```)"
    elif not has_example_section:
        fix = "Add an '## Examples' section to organize your code samples"
    else:
        fix = ""

    return CheckResult(
        name="has_examples",
        description="Has code examples with Examples section",
        passed=passed,
        points=20 if passed else 0,
        max=20,
        fix=fix,
    )


def _check_anti_patterns(body: str) -> CheckResult:
    """Check for anti-patterns/mistakes section."""
    passed = bool(_ANTIPATTERN_PATTERNS.search(body))

    return CheckResult(
        name="has_anti_patterns",
        description="Has 'mistakes to avoid' section",
        passed=passed,
        points=15 if passed else 0,
        max=15,
        fix="Add a '## Common Mistakes to Avoid' section"
        if not passed
        else "",
    )


def _check_imperative_language(body: str) -> CheckResult:
    """Check usage of imperative vs vague language."""
    imperative_count = len(_IMPERATIVE_WORDS.findall(body))
    vague_count = len(_VAGUE_WORDS.findall(body))

    # Good: more imperative than vague, or at least some imperative
    passed = imperative_count >= 3 and imperative_count > vague_count

    fix = ""
    if not passed:
        if imperative_count < 3:
            fix = (
                "Use more imperative language: "
                "'Always X', 'Never Y', 'Must Z'"
            )
        elif vague_count >= imperative_count:
            # Find first vague usage for specific feedback
            match = _VAGUE_WORDS.search(body)
            word = match.group(0) if match else "consider"
            fix = (
                f"Replace vague language ('{word}...') "
                "with direct rules ('Always...', 'Never...')"
            )

    return CheckResult(
        name="uses_imperative",
        description="Uses imperative language (Always/Never/Must)",
        passed=passed,
        points=10 if passed else 0,
        max=10,
        fix=fix,
    )


def _check_no_placeholders(body: str) -> CheckResult:
    """Check for leftover placeholder comments."""
    match = _PLACEHOLDER_PATTERNS.search(body)
    passed = match is None

    fix = ""
    if not passed and match:
        fix = f"Remove placeholder: '{match.group(0).strip()}'"

    return CheckResult(
        name="no_placeholders",
        description="No TODO or placeholder comments",
        passed=passed,
        points=5 if passed else 0,
        max=5,
        fix=fix,
    )


# ── Main lint function ──


def lint_skill(skill_path: Path) -> LintResult:
    """Lint a skill directory or SKILL.md file.

    Returns LintResult with score and individual check results.
    """
    # Resolve to SKILL.md
    if skill_path.is_dir():
        md_path = skill_path / "SKILL.md"
    else:
        md_path = skill_path

    if not md_path.exists():
        return LintResult(
            slug=skill_path.name,
            path=str(skill_path),
            score=0,
            max_score=100,
            checks=[
                CheckResult(
                    name="file_exists",
                    description="SKILL.md file exists",
                    passed=False,
                    points=0,
                    max=100,
                    fix=f"Create SKILL.md at {md_path}",
                )
            ],
        )

    text = md_path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)

    checks = [
        _check_frontmatter(fm),
        _check_description_quality(fm),
        _check_triggers(body),
        _check_principles(body),
        _check_examples(body),
        _check_anti_patterns(body),
        _check_imperative_language(body),
        _check_no_placeholders(body),
    ]

    score = sum(c.points for c in checks)
    max_score = sum(c.max for c in checks)

    return LintResult(
        slug=skill_path.name if skill_path.is_dir() else skill_path.stem,
        path=str(md_path),
        score=score,
        max_score=max_score,
        checks=checks,
    )


def lint_result_to_dict(result: LintResult) -> dict:
    """Convert LintResult to JSON-serializable dict."""
    return {
        "slug": result.slug,
        "path": result.path,
        "score": result.score,
        "max_score": result.max_score,
        "checks": [
            {
                "name": c.name,
                "description": c.description,
                "passed": c.passed,
                "points": c.points,
                "max": c.max,
                "fix": c.fix,
            }
            for c in result.checks
        ],
    }
