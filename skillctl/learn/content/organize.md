---
title: Organizing Your Skills Library
subtitle: Structure, naming, and tagging for discoverability
order: 3
next: examples
---

A well-organized skills library lets agents find the right skill fast.
Structure by domain, name for clarity, tag for search.

## Directory Structure

Group skills by their scope and purpose. Core skills are always active.
Domain skills activate based on context.

### tree

.claude/skills/
  core/                Always-active standards
    sql-standards/
      SKILL.md
    code-style/
      SKILL.md
  modeling/            Domain-specific patterns
    data-vault/
      SKILL.md
    dimensional/
      SKILL.md
  platforms/           Platform-specific guides
    databricks/
      SKILL.md
    snowflake/
      SKILL.md
  tools/               Tool-specific skills
    dbt/
      SKILL.md
    spark/
      SKILL.md

### points

- core/ = always loaded, low overhead
- Domain folders activate by context
- One SKILL.md per skill directory
- Keep the tree shallow (2 levels max)

## Naming Conventions

Skill names should be scannable, sortable, and self-documenting.

### table

| Pattern | Example | When to Use |
|---|---|---|
| {domain}-{topic} | sql-standards | General standards |
| {tool}-{action} | dbt-testing | Tool workflows |
| {platform}-{feature} | snowflake-clustering | Platform features |
| {methodology} | data-vault | Full methodologies |

### points

- Use lowercase kebab-case: my-skill not My_Skill
- Lead with the most specific word
- Avoid generic prefixes: best-practices-sql vs sql-standards
- Keep it short: 2-3 words maximum

## Tagging Strategy

Tags power search. Use a consistent vocabulary across all skills.

### tags

- Methodology: data-vault, dimensional, anchor, kimball
- Platform: databricks, snowflake, bigquery, postgres
- Tool: dbt, spark, airflow, dagster
- Domain: modeling, testing, quality, governance
- Scope: core, team, project

### points

- Use existing tags before creating new ones
- 3-5 tags per skill is the sweet spot
- Tags are lowercase, hyphenated
- First tag should be the primary category

## Lifecycle

Skills are living documents. Review and update them regularly.

### stages

1. Draft    — Initial version, may have gaps
2. Active   — Reviewed, tested, in daily use
3. Review   — Scheduled for update or validation
4. Retired  — Superseded, kept for reference

### points

- Set a review date in frontmatter: review_by: 2026-06-01
- Archive retired skills, don't delete them
- Track which skills the agent uses most
- Update when the agent produces wrong output
