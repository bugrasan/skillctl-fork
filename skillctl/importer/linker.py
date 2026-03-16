"""Symlink management for installed skills."""

import os
import shutil
from pathlib import Path


def create_symlink(source: Path, target: Path) -> None:
    """Create a symlink: target -> source.

    Args:
        source: The actual skill directory (in repos/)
        target: Where the symlink should appear (in skills dir)
    """
    if target.exists() or target.is_symlink():
        if target.is_symlink():
            current = target.resolve()
            if current == source.resolve():
                return  # Already correctly linked
            target.unlink()
        else:
            raise FileExistsError(
                f"Target path exists and is not a symlink: {target}"
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(source, target)


def remove_symlink(target: Path) -> bool:
    """Remove a symlink. Returns True if removed."""
    if target.is_symlink():
        target.unlink()
        return True
    return False


def remove_clone(clone_path: Path) -> bool:
    """Remove a cloned repository. Returns True if removed."""
    if clone_path.exists():
        shutil.rmtree(clone_path)
        return True
    return False
