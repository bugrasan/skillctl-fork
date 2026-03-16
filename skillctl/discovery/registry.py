"""Registry-based skill discovery — fetch from trusted skill repos.

Uses content-addressed caching: each skill's Git blob SHA is stored
alongside its enrichment. On refresh, only new/changed skills are
fetched and enriched. Unchanged skills carry forward their cached
enrichment data, costing zero LLM calls.
"""

import json
import time
from pathlib import Path
from typing import Optional

import httpx
import yaml

from .. import __version__

from ..config import Config, SKILLCTL_DIR
from .enrichment import enrich_skills_batch

GITHUB_API = "https://api.github.com"
CACHE_DIR = SKILLCTL_DIR / "cache" / "registries"


# ── GitHub helpers ──


def _get_headers(config: Config) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"skillctl/{__version__}",
    }
    if config.github_token:
        headers["Authorization"] = f"Bearer {config.github_token}"
    return headers


def _fetch_skill_md_raw(
    client: httpx.Client,
    registry: str,
    skill_path: str,
    branch: str = "main",
) -> Optional[str]:
    url = f"https://raw.githubusercontent.com/{registry}/{branch}/{skill_path}"
    try:
        resp = client.get(
            url, headers={"User-Agent": f"skillctl/{__version__}"}
        )
        if resp.status_code == 200:
            return resp.text
    except (httpx.HTTPError, httpx.TimeoutException):
        pass
    return None


def _parse_skill_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


# ── Cache with SHA tracking ──


def _cache_path(registry: str) -> Path:
    safe_name = registry.replace("/", "__")
    return CACHE_DIR / f"{safe_name}.json"


def _load_cache_full(registry: str) -> Optional[dict]:
    """Load full cache data (including metadata) regardless of TTL."""
    path = _cache_path(registry)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _load_cache_if_fresh(registry: str, ttl: int) -> Optional[list[dict]]:
    """Load cached skills if TTL hasn't expired."""
    data = _load_cache_full(registry)
    if data and time.time() - data.get("fetched_at", 0) < ttl:
        return data.get("skills", [])
    return None


def _save_cache(
    registry: str, skills: list[dict], enriched: bool = False
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(registry)
    data = {
        "registry": registry,
        "fetched_at": time.time(),
        "skill_count": len(skills),
        "enriched": enriched,
        "skills": skills,
    }
    path.write_text(json.dumps(data, indent=2, default=str))


# ── Validation ──

MIN_SKILLS_FOR_REGISTRY = 2

# Required YAML frontmatter fields for a valid skill
_REQUIRED_FRONTMATTER = {"name", "description"}


def validate_registry(config: Config, repo: str) -> dict:
    """Validate that a repo is a legitimate skills registry.

    Checks:
    1. Repo exists and is accessible
    2. Has 2+ SKILL.md files in subdirectories (not root-level)
    3. Sample SKILL.md has valid YAML frontmatter with name + description

    Returns a dict with:
      valid: bool
      skills: int
      reason: str
      suggestion: str | None
    """
    headers = _get_headers(config)

    try:
        with httpx.Client(timeout=15) as client:
            # 1. Check repo exists
            resp = client.get(
                f"{GITHUB_API}/repos/{repo}", headers=headers
            )
            if resp.status_code == 404:
                return {
                    "valid": False,
                    "skills": 0,
                    "reason": f"Repository not found: {repo}",
                    "suggestion": None,
                }
            if resp.status_code != 200:
                return {
                    "valid": False,
                    "skills": 0,
                    "reason": f"Cannot access repository: HTTP {resp.status_code}",
                    "suggestion": None,
                }

            branch = resp.json().get("default_branch", "main")

            # 2. Get tree — find SKILL.md files
            tree_resp = client.get(
                f"{GITHUB_API}/repos/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
                headers=headers,
            )
            if tree_resp.status_code != 200:
                return {
                    "valid": False,
                    "skills": 0,
                    "reason": "Cannot read repository tree",
                    "suggestion": None,
                }

            tree = tree_resp.json().get("tree", [])

            # SKILL.md in subdirectories (the registry pattern)
            skill_paths = [
                item["path"]
                for item in tree
                if item["path"].endswith("/SKILL.md")
                and item["type"] == "blob"
                and not item["path"].startswith("template/")
            ]

            # Root-level SKILL.md (single skill, not a registry)
            has_root_skill = any(
                item["path"] == "SKILL.md" and item["type"] == "blob"
                for item in tree
            )

            if not skill_paths and not has_root_skill:
                return {
                    "valid": False,
                    "skills": 0,
                    "reason": f"No SKILL.md files found in {repo}",
                    "suggestion": None,
                }

            if not skill_paths and has_root_skill:
                return {
                    "valid": False,
                    "skills": 1,
                    "reason": (
                        f"{repo} has a single SKILL.md at root — "
                        "this is a skill, not a registry"
                    ),
                    "suggestion": f"skillctl install {repo}",
                }

            if len(skill_paths) < MIN_SKILLS_FOR_REGISTRY:
                return {
                    "valid": False,
                    "skills": len(skill_paths),
                    "reason": (
                        f"{repo} only has {len(skill_paths)} skill — "
                        f"registries need at least {MIN_SKILLS_FOR_REGISTRY}"
                    ),
                    "suggestion": f"skillctl install {repo}",
                }

            # 3. Spot-check: fetch first SKILL.md and validate frontmatter
            sample_path = skill_paths[0]
            raw = _fetch_skill_md_raw(
                client, repo, sample_path, branch
            )
            if raw:
                meta = _parse_skill_frontmatter(raw)
                missing = _REQUIRED_FRONTMATTER - set(
                    k for k, v in meta.items() if v
                )
                if missing:
                    return {
                        "valid": False,
                        "skills": len(skill_paths),
                        "reason": (
                            f"SKILL.md in {repo} is missing required "
                            f"frontmatter: {', '.join(sorted(missing))}"
                        ),
                        "suggestion": None,
                    }

            return {
                "valid": True,
                "skills": len(skill_paths),
                "reason": "",
                "suggestion": None,
            }

    except (httpx.HTTPError, httpx.TimeoutException) as e:
        return {
            "valid": False,
            "skills": 0,
            "reason": f"Network error: {e}",
            "suggestion": None,
        }


# ── Core fetch with incremental enrichment ──


def fetch_registry(config: Config, registry: str) -> list[dict]:
    """Fetch skills from a registry with SHA-based incremental enrichment.

    Flow:
    1. If cache is fresh (within TTL), return it immediately.
    2. Otherwise, fetch the Git tree to get current SHAs.
    3. Compare SHAs against cached SHAs.
    4. Only fetch raw content for new/changed skills.
    5. Only enrich new/changed skills via LLM.
    6. Carry forward cached enrichment for unchanged skills.
    """
    # Fast path: cache is fresh
    fresh = _load_cache_if_fresh(registry, config.cache_ttl)
    if fresh is not None:
        return fresh

    # Load stale cache for SHA comparison (may be None on first run)
    stale_cache = _load_cache_full(registry)
    cached_skills_by_slug: dict[str, dict] = {}
    if stale_cache:
        for s in stale_cache.get("skills", []):
            cached_skills_by_slug[s.get("slug", "")] = s

    headers = _get_headers(config)
    skills: list[dict] = []
    new_raw_contents: dict[str, str] = {}  # Only new/changed skills

    try:
        with httpx.Client(timeout=15) as client:
            # Get default branch
            repo_resp = client.get(
                f"{GITHUB_API}/repos/{registry}",
                headers=headers,
            )
            if repo_resp.status_code != 200:
                # Network error — return stale cache if available
                if cached_skills_by_slug:
                    return list(cached_skills_by_slug.values())
                return []
            repo_data = repo_resp.json()
            branch = repo_data.get("default_branch", "main")
            repo_stars = repo_data.get("stargazers_count", 0)

            # Get full tree (1 API call) — includes SHA per file
            tree_resp = client.get(
                f"{GITHUB_API}/repos/{registry}/git/trees/{branch}",
                params={"recursive": "1"},
                headers=headers,
            )
            if tree_resp.status_code != 200:
                if cached_skills_by_slug:
                    return list(cached_skills_by_slug.values())
                return []

            tree = tree_resp.json().get("tree", [])

            # Find SKILL.md entries with their Git SHAs
            skill_entries = [
                item
                for item in tree
                if item["path"].endswith("/SKILL.md")
                and item["type"] == "blob"
                and not item["path"].startswith("template/")
            ]

            for entry in skill_entries:
                skill_path = entry["path"]
                git_sha = entry.get("sha", "")
                skill_dir = str(Path(skill_path).parent)
                slug = Path(skill_dir).name

                cached = cached_skills_by_slug.get(slug)

                # Check if SHA matches cache — skill unchanged
                if cached and cached.get("content_sha") == git_sha:
                    # Carry forward cached entry, update stars
                    cached["stars"] = repo_stars
                    skills.append(cached)
                    continue

                # New or changed skill — fetch content
                raw = _fetch_skill_md_raw(
                    client, registry, skill_path, branch
                )
                if not raw:
                    continue

                meta = _parse_skill_frontmatter(raw)
                new_raw_contents[slug] = raw

                skills.append(
                    {
                        "name": meta.get("name") or slug,
                        "slug": slug,
                        "source": "registry",
                        "registry": registry,
                        "description": meta.get("description") or "",
                        "tags": meta.get("tags") or [],
                        "author": meta.get("author") or "",
                        "path_in_repo": skill_dir,
                        "repo": registry,
                        "installed": False,
                        "content_sha": git_sha,
                        "stars": repo_stars,
                    }
                )

    except (httpx.HTTPError, httpx.TimeoutException):
        if cached_skills_by_slug:
            return list(cached_skills_by_slug.values())
        return []

    # Enrich ONLY new/changed skills
    enriched = any(s.get("keywords") for s in skills)
    if new_raw_contents:
        # Build list of just the new/changed skill dicts
        new_skills = [
            s for s in skills if s.get("slug") in new_raw_contents
        ]
        enriched_new = enrich_skills_batch(new_skills, new_raw_contents)

        # Merge enriched data back
        enriched_map = {s["slug"]: s for s in enriched_new}
        skills = [
            enriched_map.get(s["slug"], s) for s in skills
        ]
        enriched = any(s.get("keywords") for s in skills)

    if skills:
        _save_cache(registry, skills, enriched=enriched)

    return skills


# ── Search ──


def search_registries(
    config: Config, query: str
) -> list[dict]:
    """Search all configured registries with scored ranking."""
    all_skills: list[dict] = []

    for registry in config.registries:
        registry_skills = fetch_registry(config, registry)
        all_skills.extend(registry_skills)

    if not query.strip():
        return all_skills

    scored = []
    for skill in all_skills:
        score = _score_skill(skill, query)
        if score > 0:
            scored.append((score, skill))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return []

    top_score = scored[0][0]
    threshold = max(top_score * 0.2, 10)
    return [skill for s, skill in scored if s >= threshold]


# ── Scoring ──

# Maps user search terms → skill slugs only.
_SYNONYMS: dict[str, list[str]] = {
    "excel": ["xlsx"],
    "spreadsheet": ["xlsx"],
    "csv": ["xlsx"],
    "tsv": ["xlsx"],
    "word": ["docx"],
    "powerpoint": ["pptx"],
    "slides": ["pptx"],
    "presentation": ["pptx"],
    "deck": ["pptx"],
    "figma": ["frontend-design", "canvas-design"],
    "canva": ["canvas-design"],
    "sketch": ["canvas-design", "frontend-design"],
    "poster": ["canvas-design"],
    "website": ["frontend-design", "web-artifacts-builder"],
    "landing": ["frontend-design"],
    "html": ["frontend-design", "web-artifacts-builder"],
    "css": ["frontend-design"],
    "nextjs": ["vercel-react-best-practices"],
    "vercel": ["deploy-to-vercel"],
    "playwright": ["webapp-testing"],
    "selenium": ["webapp-testing"],
    "cypress": ["webapp-testing"],
    "sdk": ["claude-api"],
    "anthropic": ["claude-api"],
    "gif": ["slack-gif-creator"],
    "animation": ["slack-gif-creator"],
    "generative": ["algorithmic-art"],
    "brand": ["brand-guidelines"],
    "memo": ["docx", "internal-comms"],
    "report": ["docx", "internal-comms"],
    "newsletter": ["internal-comms"],
    "ocr": ["pdf"],
    "mobile": ["vercel-react-native-skills"],
    "expo": ["vercel-react-native-skills"],
    "docs": ["doc-coauthoring"],
    "spec": ["doc-coauthoring"],
    "proposal": ["doc-coauthoring"],
}

_STOP_WORDS = {
    "a", "an", "the", "my", "your", "our", "this", "that",
    "i", "me", "we", "it", "its",
    "to", "for", "in", "on", "at", "of", "with", "from", "by",
    "is", "are", "was", "be", "do", "does", "did",
    "can", "could", "will", "would", "should",
    "how", "what", "which", "who", "where", "when",
    "and", "or", "but", "not", "no", "so",
    "make", "create", "build", "write", "generate", "get",
    "use", "using", "want", "need", "help", "please",
    "some", "something", "thing", "app", "file", "files",
}


def _expand_query(query_words: list[str]) -> list[str]:
    expanded = list(query_words)
    for word in query_words:
        for syn in _SYNONYMS.get(word, []):
            if syn not in expanded:
                expanded.append(syn)
    return expanded


def _score_skill(skill: dict, query: str) -> float:
    query_lower = query.lower()
    query_words = [
        w for w in query_lower.split() if w not in _STOP_WORDS
    ]
    if not query_words:
        query_words = query_lower.split()
    expanded_words = _expand_query(query_words)
    score = 0.0

    slug = (skill.get("slug") or "").lower()
    name = (skill.get("name") or "").lower()
    desc = (skill.get("description") or "").lower()
    short_desc = (skill.get("short_desc") or "").lower()
    tags = [t.lower() for t in (skill.get("tags") or [])]
    keywords = [k.lower() for k in (skill.get("keywords") or [])]
    use_cases = " ".join(
        u.lower() for u in (skill.get("use_cases") or [])
    )

    for word in query_words:
        if word == slug:
            score += 100
        elif word in slug:
            score += 50
        if word in name:
            score += 40
        if any(word == kw for kw in keywords):
            score += 60
        elif any(word in kw for kw in keywords):
            score += 30
        if any(word == t for t in tags):
            score += 35
        elif any(word in t for t in tags):
            score += 15
        if word in use_cases:
            score += 25
        if word in short_desc:
            score += 20
        if word in desc:
            score += 5

    synonym_words = [w for w in expanded_words if w not in query_words]
    for word in synonym_words:
        if word == slug:
            score += 45
        elif word in slug:
            score += 20
        if word in name:
            score += 15
        if any(word == kw for kw in keywords):
            score += 25
        if any(word == t for t in tags):
            score += 15
        if word in desc:
            score += 3

    return score
