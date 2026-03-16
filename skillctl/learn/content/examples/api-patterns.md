---
name: api-patterns
description: REST API design patterns — endpoints, errors, pagination, and auth
tags: [api, rest, patterns, development]
author: platform-team
version: 1.0.0
---

# REST API Design Patterns

Patterns for building consistent, well-documented REST APIs.

## When to Use This Skill

Use this skill when:
- The user asks to create or modify API endpoints
- You see route handlers, controllers, or API middleware
- The user mentions REST, endpoints, or HTTP methods
- You are working in files matching: routes/*.py, api/*.ts, controllers/*

## Core Principles

- Use plural nouns for resources: /users not /user
- Use HTTP methods for actions: GET reads, POST creates, PUT replaces, PATCH updates, DELETE removes
- Always return consistent error shapes with code, message, and details
- Always paginate list endpoints — never return unbounded results
- Always version the API in the URL path: /v1/users
- Never expose internal IDs or database structure in response payloads

## Step-by-Step Process

1. Define the resource and its relationships
2. Map CRUD operations to HTTP methods
3. Define request/response schemas
4. Add input validation at the boundary
5. Add pagination for list endpoints
6. Add error handling with consistent shapes
7. Document with OpenAPI/Swagger

## Common Mistakes to Avoid

Bad: Verbs in URLs
```
POST /api/createUser
GET /api/getUserById/123
```

Good: Nouns with HTTP methods
```
POST /api/v1/users
GET /api/v1/users/123
```

Bad: Inconsistent error responses
```json
{"error": "not found"}
{"message": "Bad request", "status": 400}
{"err": {"code": 500}}
```

Good: Consistent error envelope
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User 123 not found",
    "details": {}
  }
}
```

## Examples

### Paginated list endpoint
```python
@router.get("/v1/users")
async def list_users(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    users = await db.fetch_users(limit=limit, offset=offset)
    total = await db.count_users()
    return {
        "data": users,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
        },
    }
```

### Error handling middleware
```python
@app.exception_handler(AppError)
async def handle_app_error(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
```
