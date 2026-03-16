"""Configuration management for skillctl."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

SKILLCTL_DIR = Path.home() / ".skillctl"
CONFIG_PATH = SKILLCTL_DIR / "config.yaml"

DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"
DEFAULT_REPOS_DIR = SKILLCTL_DIR / "repos"

DEFAULT_REGISTRIES = [
    "anthropics/skills",
    "vercel-labs/agent-skills",
]

VALID_KEYS = [
    "skills_dir",
    "repos_dir",
    "scan_paths",
    "registries",
    "github_token",
    "default_format",
    "cache_ttl",
]


@dataclass
class Config:
    skills_dir: str = str(DEFAULT_SKILLS_DIR)
    repos_dir: str = str(DEFAULT_REPOS_DIR)
    scan_paths: list[str] = field(default_factory=list)
    registries: list[str] = field(default_factory=lambda: list(DEFAULT_REGISTRIES))
    github_token: Optional[str] = None
    default_format: str = "table"
    cache_ttl: int = 3600

    @property
    def skills_path(self) -> Path:
        return Path(self.skills_dir).expanduser()

    @property
    def repos_path(self) -> Path:
        return Path(self.repos_dir).expanduser()

    def get_scan_paths(self) -> list[Path]:
        return [Path(p).expanduser() for p in self.scan_paths]


def _detect_gh_token() -> Optional[str]:
    """Try to get GitHub token from gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def load_config() -> Config:
    """Load config from file, falling back to defaults."""
    # Explicitly reference module constants so they're patchable in tests
    config = Config(
        skills_dir=str(DEFAULT_SKILLS_DIR),
        repos_dir=str(DEFAULT_REPOS_DIR),
    )

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                data = yaml.safe_load(f) or {}

            for key in ("skills_dir", "repos_dir", "default_format"):
                if key in data:
                    setattr(config, key, data[key])
            if "scan_paths" in data:
                config.scan_paths = data["scan_paths"] or []
            if "registries" in data:
                config.registries = data["registries"] or list(DEFAULT_REGISTRIES)
            if "github_token" in data and data["github_token"]:
                config.github_token = data["github_token"]
            if "cache_ttl" in data:
                config.cache_ttl = int(data["cache_ttl"])
        except (yaml.YAMLError, OSError):
            pass

    # Auto-detect GitHub token if not explicitly configured
    if not config.github_token:
        config.github_token = _detect_gh_token()

    return config


def save_config(config: Config) -> None:
    """Save config to file. Does not persist auto-detected github_token."""
    SKILLCTL_DIR.mkdir(parents=True, exist_ok=True)

    # Read existing to preserve explicit github_token
    existing_token = None
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                existing = yaml.safe_load(f) or {}
            existing_token = existing.get("github_token")
        except (yaml.YAMLError, OSError):
            pass

    data: dict = {
        "skills_dir": config.skills_dir,
        "repos_dir": config.repos_dir,
        "scan_paths": config.scan_paths,
        "registries": config.registries,
        "default_format": config.default_format,
        "cache_ttl": config.cache_ttl,
    }

    # Only persist token if it was already in the file or explicitly set
    if existing_token:
        data["github_token"] = existing_token

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def set_config_value(key: str, value: str) -> Config:
    """Set a single config value and save."""
    config = load_config()

    if key == "skills_dir":
        config.skills_dir = value
    elif key == "repos_dir":
        config.repos_dir = value
    elif key == "scan_paths":
        config.scan_paths = [p.strip() for p in value.split(",") if p.strip()]
    elif key == "github_token":
        config.github_token = value
        # Explicitly save token to file
        save_config(config)
        # Re-read and set to ensure it's persisted
        SKILLCTL_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_PATH) as f:
                data = yaml.safe_load(f) or {}
            data["github_token"] = value
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except (yaml.YAMLError, OSError):
            pass
        return config
    elif key == "default_format":
        if value not in ("table", "json"):
            raise ValueError(f"Invalid format: {value}. Must be 'table' or 'json'.")
        config.default_format = value
    elif key == "registries":
        config.registries = [r.strip() for r in value.split(",") if r.strip()]
    elif key == "cache_ttl":
        config.cache_ttl = int(value)
    else:
        raise ValueError(
            f"Unknown config key: {key}. Valid keys: {', '.join(VALID_KEYS)}"
        )

    save_config(config)
    return config
