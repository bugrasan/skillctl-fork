---
title: Writing for AI Comprehension
subtitle: Rules for content the agent will actually follow
order: 2
next: organize
---

Skills are read by AI, not just humans. The agent treats vague
language as optional. Be direct, specific, and concrete.

## Use imperative language

The agent follows commands, not suggestions. Hedge words like "consider"
or "might" signal that a rule is optional.

### dont

- Consider using CTEs for better readability
- You might want to name your CTEs descriptively
- It can be helpful to specify JOIN types

### do

- Always use CTEs instead of subqueries
- Name every CTE descriptively (not cte1, cte2)
- Never omit the JOIN type keyword

## Provide concrete examples

Abstract advice produces abstract code. Show the exact pattern you want.

### dont

- Use good naming conventions
- Follow best practices for column names
- Structure your queries well

### do

- Name columns: user_id not uid, created_at not ts
- Prefix boolean columns with is_ or has_
- Put each SELECT column on its own line

## State rules, not suggestions

Every sentence should be a clear directive. If the agent can't
determine whether a rule applies, it will skip it.

### dont

- You may want to consider adding indexes
- It's generally a good idea to add comments
- Some teams prefer snake_case for table names

### do

- Add an index on every foreign key column
- Add a comment on columns with non-obvious names
- Use snake_case for all table and column names

## Include decision trees

When the right approach depends on context, give the agent a
decision framework instead of a single rule.

### example

```markdown
## Choosing a Model Type
- If data changes in place → SCD Type 1 (overwrite)
- If you need history of changes → SCD Type 2 (add row)
- If only latest + previous matter → SCD Type 3 (add column)
- When unsure → default to SCD Type 2
```

### points

- Use if/then patterns the agent can evaluate
- Always include a default/fallback case
- Order from most common to least common
