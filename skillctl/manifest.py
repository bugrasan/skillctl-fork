"""Manifest management — tracks installed skills."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import SKILLCTL_DIR

MANIFEST_PATH = SKILLCTL_DIR / "manifest.json"


def _load_raw() -> dict:
    """Load raw manifest data."""
    if not MANIFEST_PATH.exists():
        return {"skills": {}}
    try:
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"skills": {}}


def _save_raw(data: dict) -> None:
    """Save raw manifest data."""
    SKILLCTL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=2, sort_keys=False)
        f.write("\n")


def list_skills() -> list[dict]:
    """List all installed skills."""
    data = _load_raw()
    return list(data.get("skills", {}).values())


def get_skill(slug: str) -> Optional[dict]:
    """Get a skill by slug."""
    data = _load_raw()
    return data.get("skills", {}).get(slug)


def add_skill(slug: str, skill_data: dict) -> None:
    """Add or update a skill in the manifest."""
    data = _load_raw()
    if "skills" not in data:
        data["skills"] = {}
    skill_data["installed_at"] = datetime.now(timezone.utc).isoformat()
    data["skills"][slug] = skill_data
    _save_raw(data)


def remove_skill(slug: str) -> bool:
    """Remove a skill from the manifest. Returns True if it existed."""
    data = _load_raw()
    if slug in data.get("skills", {}):
        del data["skills"][slug]
        _save_raw(data)
        return True
    return False


def update_skill(slug: str, updates: dict) -> bool:
    """Update fields of an existing skill. Returns True if found."""
    data = _load_raw()
    if slug in data.get("skills", {}):
        data["skills"][slug].update(updates)
        _save_raw(data)
        return True
    return False


def is_installed(slug: str) -> bool:
    """Check if a skill is installed."""
    data = _load_raw()
    return slug in data.get("skills", {})
