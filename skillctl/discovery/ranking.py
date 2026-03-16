"""Merge and rank search results."""

from .. import manifest


def merge_and_rank(
    local_results: list[dict],
    github_results: list[dict],
    sort: str = "stars",
) -> list[dict]:
    """Merge local and GitHub results, mark installed status, rank."""
    installed_slugs = {s["slug"] for s in manifest.list_skills()}

    for result in github_results:
        slug = result.get("slug", "")
        result["installed"] = slug in installed_slugs

    # Local results first, then GitHub — deduplicate by slug
    seen: set[str] = set()
    local: list[dict] = []
    for r in local_results:
        key = r.get("slug", r.get("name", ""))
        if key not in seen:
            seen.add(key)
            local.append(r)

    remote: list[dict] = []
    for r in github_results:
        key = r.get("slug", r.get("name", ""))
        if key not in seen:
            seen.add(key)
            remote.append(r)

    # Sort remote results
    if sort == "name":
        remote.sort(key=lambda r: r.get("name", ""))
    elif sort == "updated":
        remote.sort(key=lambda r: r.get("updated", ""), reverse=True)
    else:
        remote.sort(key=lambda r: r.get("stars", 0), reverse=True)

    return local + remote
