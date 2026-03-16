"""Git operations — clone, pull, get commit SHA."""

import subprocess
from pathlib import Path


def clone_repo(repo: str, dest: Path) -> str:
    """Clone a GitHub repo (shallow). Returns the commit SHA."""
    url = f"https://github.com/{repo}.git"

    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "not found" in stderr.lower() or "does not exist" in stderr.lower():
            raise RuntimeError(f"Repository not found: {repo}")
        raise RuntimeError(f"Clone failed: {stderr}")

    return get_commit_sha(dest)


def pull_repo(repo_path: Path) -> tuple[str, str]:
    """Pull latest changes. Returns (old_sha, new_sha)."""
    old_sha = get_commit_sha(repo_path)

    # Unshallow if needed for pull to work
    result = subprocess.run(
        ["git", "-C", str(repo_path), "pull", "--ff-only"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Pull failed: {result.stderr.strip()}")

    new_sha = get_commit_sha(repo_path)
    return old_sha, new_sha


def get_commit_sha(repo_path: Path) -> str:
    """Get the current HEAD commit SHA (short)."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    """Check if a path is a git repository."""
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.returncode == 0
