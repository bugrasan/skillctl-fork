---
name: sql-standards
description: SQL coding standards — formatting, CTEs, JOINs, and naming
tags: [sql, standards, core]
author: data-platform-team
version: 1.0.0
---

# SQL Coding Standards

Standards for writing clean, consistent, reviewable SQL across all projects.

## When to Use This Skill

Use this skill when:
- The user asks you to write, review, or modify SQL
- You see .sql files, dbt models, or database migrations
- The user mentions queries, tables, views, or stored procedures

## Core Principles

- Always use UPPERCASE for SQL keywords (SELECT, FROM, WHERE, JOIN)
- Always use lowercase snake_case for identifiers (table names, columns)
- Indent with 4 spaces, never tabs
- One column per line in SELECT clauses
- Always specify the JOIN type (INNER JOIN, LEFT JOIN — never bare JOIN)
- Always alias tables with meaningful short names (users u, orders o)

## Step-by-Step Process

1. Start with a CTE block for data preparation
2. Name each CTE after what it contains (active_users, recent_orders)
3. Write the final SELECT from the prepared CTEs
4. Add comments only for non-obvious business logic

## Common Mistakes to Avoid

Bad: SELECT * with implicit joins
```sql
SELECT * FROM users, orders WHERE users.id = orders.user_id
```

Good: Explicit columns with explicit joins
```sql
SELECT
    u.id,
    u.name,
    o.total_amount
FROM users u
INNER JOIN orders o ON o.user_id = u.id
```

Bad: Deeply nested subqueries
```sql
SELECT * FROM (SELECT * FROM (SELECT ...))
```

Good: Flat CTE chain
```sql
WITH
    base_users AS (
        SELECT id, name FROM users WHERE active = true
    ),
    user_orders AS (
        SELECT user_id, COUNT(*) AS order_count
        FROM orders
        GROUP BY user_id
    )
SELECT
    b.id,
    b.name,
    COALESCE(uo.order_count, 0) AS order_count
FROM base_users b
LEFT JOIN user_orders uo ON uo.user_id = b.id
```

## Examples

### Simple query
```sql
SELECT
    u.id,
    u.name,
    u.email,
    u.created_at
FROM users u
WHERE u.active = true
ORDER BY u.created_at DESC
LIMIT 100
```

### Aggregation with CTEs
```sql
WITH
    monthly_revenue AS (
        SELECT
            DATE_TRUNC('month', order_date) AS month,
            SUM(total_amount) AS revenue
        FROM orders
        WHERE order_date >= DATEADD('year', -1, CURRENT_DATE)
        GROUP BY DATE_TRUNC('month', order_date)
    )
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100,
        1
    ) AS growth_pct
FROM monthly_revenue
ORDER BY month
```
