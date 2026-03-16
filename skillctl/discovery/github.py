"""GitHub-based skill discovery."""

import logging
from typing import Optional

import httpx

from .. import __version__
from ..config import Config

log = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
SEARCH_REPOS = f"{GITHUB_API}/search/repositories"
SEARCH_CODE = f"{GITHUB_API}/search/code"


class GitHubRateLimitError(Exception):
    """Raised when GitHub API rate limit is hit."""

    pass


def _get_headers(config: Config) -> dict:
    """Get HTTP headers for GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"skillctl/{__version__}",
    }
    if config.github_token:
        headers["Authorization"] = f"Bearer {config.github_token}"
    return headers


def _check_rate_limit(resp: httpx.Response) -> None:
    """Raise if rate limited."""
    if resp.status_code == 403:
        remaining = resp.headers.get("x-ratelimit-remaining", "")
        if remaining == "0":
            raise GitHubRateLimitError(
                "GitHub API rate limit exceeded."
                " Authenticate with: gh auth login"
            )
        raise GitHubRateLimitError(
            f"GitHub API access denied (403). Response: {resp.text[:200]}"
        )
    if resp.status_code == 422:
        raise GitHubRateLimitError(
            "GitHub API validation failed — query may be too broad."
        )


def search_github(
    config: Config, query: str, sort: str = "stars"
) -> list[dict]:
    """Search GitHub for skill repos.

    Returns results list. Raises GitHubRateLimitError on 403.
    Returns empty list on network errors.
    """
    results: list[dict] = []
    headers = _get_headers(config)
    seen: set[str] = set()

    try:
        with httpx.Client(timeout=10) as client:
            # Strategy 1: repos with agent-skill topics
            params = {
                "q": f"{query} topic:claude-skill OR topic:agent-skill",
                "sort": sort if sort in ("stars", "updated") else "stars",
                "order": "desc",
                "per_page": 20,
            }
            resp = client.get(SEARCH_REPOS, params=params, headers=headers)
            _check_rate_limit(resp)
            if resp.status_code == 200:
                for item in resp.json().get("items", []):
                    full_name = item["full_name"]
                    if full_name in seen:
                        continue
                    seen.add(full_name)
                    results.append(_repo_to_result(item))

            # Strategy 2: repos containing SKILL.md with keyword
            if len(results) < 10:
                code_params = {
                    "q": f"filename:SKILL.md {query}",
                    "per_page": 20,
                }
                resp2 = client.get(
                    SEARCH_CODE, params=code_params, headers=headers
                )
                _check_rate_limit(resp2)
                if resp2.status_code == 200:
                    for item in resp2.json().get("items", []):
                        repo = item.get("repository", {})
                        full_name = repo.get("full_name", "")
                        if full_name and full_name not in seen:
                            seen.add(full_name)
                            results.append(
                                {
                                    "name": full_name,
                                    "slug": repo.get("name", ""),
                                    "source": "github",
                                    "description": repo.get(
                                        "description", ""
                                    )
                                    or "",
                                    "stars": 0,
                                    "tags": [],
                                    "url": repo.get("html_url", ""),
                                    "updated": "",
                                    "installed": False,
                                }
                            )

    except GitHubRateLimitError:
        raise  # Let caller handle rate limit errors explicitly
    except (httpx.HTTPError, httpx.TimeoutException):
        return []

    return results


def get_repo_info(config: Config, repo: str) -> Optional[dict]:
    """Get detailed info about a specific GitHub repo."""
    headers = _get_headers(config)

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{GITHUB_API}/repos/{repo}", headers=headers
            )
            _check_rate_limit(resp)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "name": data["full_name"],
                    "slug": data["name"],
                    "source": "github",
                    "description": data.get("description", "") or "",
                    "stars": data.get("stargazers_count", 0),
                    "tags": data.get("topics", []),
                    "url": data.get("html_url", ""),
                    "updated": data.get("updated_at", ""),
                    "license": (data.get("license") or {}).get(
                        "spdx_id", ""
                    ),
                    "default_branch": data.get("default_branch", "main"),
                }
            elif resp.status_code == 404:
                return None
    except GitHubRateLimitError:
        raise
    except (httpx.HTTPError, httpx.TimeoutException):
        return None

    return None


def _repo_to_result(item: dict) -> dict:
    """Convert GitHub API repo item to result dict."""
    return {
        "name": item["full_name"],
        "slug": item["name"],
        "source": "github",
        "description": item.get("description", "") or "",
        "stars": item.get("stargazers_count", 0),
        "tags": item.get("topics", []),
        "url": item.get("html_url", ""),
        "updated": item.get("updated_at", ""),
        "installed": False,
    }
