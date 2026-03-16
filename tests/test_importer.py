"""Tests for importer — git ops and symlink management."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from skillctl.importer.linker import create_symlink, remove_symlink, remove_clone


class TestSymlinks:
    def test_create_symlink(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        (source / "SKILL.md").write_text("# test")

        target = tmp_path / "links" / "my-skill"

        create_symlink(source, target)

        assert target.is_symlink()
        assert target.resolve() == source.resolve()
        assert (target / "SKILL.md").exists()

    def test_create_symlink_idempotent(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "link"

        create_symlink(source, target)
        create_symlink(source, target)  # Should not raise

        assert target.is_symlink()

    def test_create_symlink_relinks_different_source(self, tmp_path):
        source1 = tmp_path / "source1"
        source1.mkdir()
        source2 = tmp_path / "source2"
        source2.mkdir()
        target = tmp_path / "link"

        create_symlink(source1, target)
        assert target.resolve() == source1.resolve()

        create_symlink(source2, target)
        assert target.resolve() == source2.resolve()

    def test_create_symlink_raises_on_existing_dir(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "existing-dir"
        target.mkdir()

        with pytest.raises(FileExistsError):
            create_symlink(source, target)

    def test_remove_symlink(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "link"
        os.symlink(source, target)

        assert remove_symlink(target) is True
        assert not target.exists()

    def test_remove_nonexistent_symlink(self, tmp_path):
        assert remove_symlink(tmp_path / "nope") is False


class TestCloneRemoval:
    def test_remove_clone(self, tmp_path):
        clone = tmp_path / "repo"
        clone.mkdir()
        (clone / "file.txt").write_text("data")

        assert remove_clone(clone) is True
        assert not clone.exists()

    def test_remove_nonexistent_clone(self, tmp_path):
        assert remove_clone(tmp_path / "nope") is False


class TestGitOps:
    def test_get_commit_sha(self, tmp_path):
        from skillctl.importer.git_ops import get_commit_sha

        # Not a git repo — should return "unknown"
        sha = get_commit_sha(tmp_path)
        assert sha == "unknown"

    def test_is_git_repo_false(self, tmp_path):
        from skillctl.importer.git_ops import is_git_repo

        assert is_git_repo(tmp_path) is False

    def test_clone_repo_not_found(self, tmp_path):
        from skillctl.importer.git_ops import clone_repo

        with pytest.raises(RuntimeError):
            clone_repo(
                "nonexistent-user-abc123/nonexistent-repo-xyz789",
                tmp_path / "dest",
            )
