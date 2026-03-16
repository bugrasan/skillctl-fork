---
title: Anatomy of a Skill
subtitle: The five layers every great skill needs
order: 1
next: write
---

A skill has 5 layers. Each one teaches the agent something different.

## Frontmatter | identity

The YAML frontmatter is the skill's identity card. The agent uses it to decide
whether this skill is relevant before reading the full content.

### example

```yaml
---
name: sql-standards
description: SQL coding standards for our team
tags: [sql, standards, core]
author: data-team
version: 1.0.0
---
```

### points

- Must have: name, description
- Should have: tags, author, version
- Tags drive search — be specific

## Triggers | when

Trigger conditions tell the agent WHEN to activate this skill. Without them,
the agent guesses — and guesses wrong.

### example

```markdown
## When to Use This Skill
Use when the user asks to write or review SQL.
Activate when you see .sql files or dbt models.
```

### points

- Be specific: file patterns, keywords, user phrases
- Precise triggers = fewer false activations
- Multiple trigger types catch more cases

## Principles | rules

Core principles are the non-negotiable rules. The agent treats these as
hard constraints, not suggestions.

### example

```markdown
## Core Principles
- Always use UPPERCASE for SQL keywords
- Never use SELECT * in production queries
- Always specify JOIN type explicitly (INNER, LEFT, etc.)
```

### points

- Use imperative language: "Always X", "Never Y"
- Keep each rule to one clear sentence
- These are your guardrails

## Anti-Patterns | avoid

Anti-patterns show the agent what NOT to do. Pairing each mistake with
the correct approach makes the fix obvious.

### example

```markdown
## Common Mistakes to Avoid
- SELECT * FROM users WHERE ...
  Instead: SELECT id, name, email FROM users WHERE ...
- Using subqueries for everything
  Instead: Use CTEs for readability
```

### points

- Pair each mistake with the correction
- Use real examples from your codebase
- Show the WHY, not just the WHAT

## Examples | show

Concrete examples ground the abstract rules. The agent uses these as
templates when generating code.

### example

```sql
SELECT
    u.id,
    u.name,
    COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.name
```

### points

- Show the principles applied in real code
- Include 2-3 examples for complex skills
- Annotate non-obvious decisions
