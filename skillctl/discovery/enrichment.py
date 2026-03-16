"""LLM-powered metadata enrichment for skills.

Generates search-friendly metadata (keywords, short descriptions,
categories, use cases) from raw SKILL.md content. Runs at index time,
results cached with the registry data via SHA-based invalidation.

Providers (auto-detected from env):
  ANTHROPIC_API_KEY → Claude Haiku 4.5  (preferred — faster, cheaper)
  OPENAI_API_KEY    → GPT-5 mini via Structured Outputs
"""

import json
import logging
import os
from typing import Optional

log = logging.getLogger(__name__)

# ── Prompt ──

SYSTEM_PROMPT = """\
You are a search metadata generator for an AI agent skills registry.

For each skill given, produce search-optimized metadata as a JSON object with:
- "slug": exact skill name as given
- "short_desc": 1-line description, max 80 chars, no "Use this skill when..."
- "keywords": 8-15 lowercase terms a user might search for, including synonyms, \
related tools, file extensions, misspellings
- "category": one of: documents, design, development, testing, deployment, \
communication, data, ai-tools, other
- "use_cases": 3-5 short task phrases

Keywords MUST include non-obvious synonyms (xlsx→"excel","spreadsheet"; \
pptx→"powerpoint","slides","deck"). Think: what would someone who doesn't \
know this skill's name type into a search box?"""

CHUNK_SIZE = 5
MAX_CONTENT_PER_SKILL = 1500


# ── Pydantic schema for OpenAI Structured Outputs ──

def _get_openai_schema():
    """Lazy-load Pydantic models (only when OpenAI provider is used)."""
    from pydantic import BaseModel

    class SkillEnrichment(BaseModel):
        slug: str
        short_desc: str
        keywords: list[str]
        category: str
        use_cases: list[str]

    class EnrichmentBatch(BaseModel):
        skills: list[SkillEnrichment]

    return EnrichmentBatch


# ── Provider detection ──


def _detect_provider() -> Optional[str]:
    """Return 'anthropic', 'openai', or None based on available keys + SDKs."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401
            return "anthropic"
        except ImportError:
            log.debug("ANTHROPIC_API_KEY set but anthropic SDK not installed")
    if os.environ.get("OPENAI_API_KEY"):
        try:
            import openai  # noqa: F401
            return "openai"
        except ImportError:
            log.debug("OPENAI_API_KEY set but openai SDK not installed")
    return None


# ── Input formatting ──


def _build_user_prompt(contents: dict[str, str]) -> str:
    """Format skill contents into the user message."""
    parts = []
    for i, (slug, content) in enumerate(contents.items(), 1):
        if len(content) > MAX_CONTENT_PER_SKILL:
            content = content[:MAX_CONTENT_PER_SKILL] + "\n...(truncated)"
        parts.append(f"--- SKILL {i}: {slug} ---\n{content}")
    return "\n\n".join(parts)


# ── Provider calls ──


def _call_anthropic(client, user_prompt: str) -> list[dict]:
    """Call Claude Haiku, parse JSON array from text response."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if "```" in text:
            text = text[: text.rfind("```")]
        text = text.strip()

    data = json.loads(text)
    items = data if isinstance(data, list) else data.get("skills", [])

    return [_normalize(item) for item in items]


def _call_openai(client, user_prompt: str) -> list[dict]:
    """Call GPT-5 mini with Structured Outputs — guaranteed valid JSON."""
    schema = _get_openai_schema()

    response = client.chat.completions.parse(
        model="gpt-5-mini",
        max_completion_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=schema,
    )

    parsed = response.choices[0].message.parsed
    if parsed is None:
        return []

    return [_normalize(s.model_dump()) for s in parsed.skills]


def _normalize(item: dict) -> dict:
    """Normalize an enrichment result to consistent shape."""
    return {
        "slug": str(item.get("slug", "")),
        "short_desc": str(item.get("short_desc", ""))[:120],
        "keywords": [str(k).lower() for k in item.get("keywords", [])[:20]],
        "category": str(item.get("category", "other")),
        "use_cases": [str(u) for u in item.get("use_cases", [])[:8]],
    }


# ── Batch orchestration ──


def enrich_skills_batch(
    skills: list[dict], raw_contents: dict[str, str]
) -> list[dict]:
    """Enrich skills in chunked LLM calls.

    Chunks of CHUNK_SIZE skills are sent per call. Failed chunks are
    logged and skipped — partial enrichment is better than none.

    Returns updated skills list with enrichment merged in.
    """
    provider = _detect_provider()
    if not provider or not raw_contents:
        return skills

    # Create client once, reuse across chunks
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        call_fn = _call_anthropic
    else:
        import openai
        client = openai.OpenAI(timeout=90.0)
        call_fn = _call_openai

    slugs = list(raw_contents.keys())
    enrich_map: dict[str, dict] = {}

    for i in range(0, len(slugs), CHUNK_SIZE):
        chunk_slugs = slugs[i : i + CHUNK_SIZE]
        chunk = {s: raw_contents[s] for s in chunk_slugs}
        chunk_label = f"chunk {i // CHUNK_SIZE + 1} ({', '.join(chunk_slugs)})"

        try:
            user_prompt = _build_user_prompt(chunk)
            results = call_fn(client, user_prompt)
            for r in results:
                enrich_map[r["slug"]] = r
            log.debug(f"Enriched {chunk_label}: {len(results)} skills")
        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse LLM response for {chunk_label}: {e}")
        except Exception as e:
            log.warning(f"Enrichment failed for {chunk_label}: {type(e).__name__}: {e}")

    if not enrich_map:
        log.warning(f"No skills enriched via {provider} — all chunks failed")
        return skills

    log.info(f"Enriched {len(enrich_map)}/{len(raw_contents)} skills via {provider}")

    # Merge enrichments into skills
    return [
        {**skill, **enrich_map[skill["slug"]]}
        if skill.get("slug") in enrich_map
        else skill
        for skill in skills
    ]
