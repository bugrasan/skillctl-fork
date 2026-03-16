"""Tests for manifest CRUD."""

from skillctl import manifest


def test_empty_manifest(skill_env):
    assert manifest.list_skills() == []
    assert manifest.get_skill("foo") is None
    assert manifest.is_installed("foo") is False


def test_add_and_get(skill_env):
    manifest.add_skill("test-skill", {
        "name": "Test Skill",
        "slug": "test-skill",
        "source": "local",
    })
    skill = manifest.get_skill("test-skill")
    assert skill is not None
    assert skill["name"] == "Test Skill"
    assert skill["source"] == "local"
    assert "installed_at" in skill


def test_list_skills(skill_env):
    manifest.add_skill("a", {"slug": "a", "source": "local"})
    manifest.add_skill("b", {"slug": "b", "source": "github"})
    skills = manifest.list_skills()
    assert len(skills) == 2


def test_remove_skill(skill_env):
    manifest.add_skill("temp", {"slug": "temp"})
    assert manifest.is_installed("temp")
    assert manifest.remove_skill("temp") is True
    assert manifest.is_installed("temp") is False
    assert manifest.remove_skill("temp") is False


def test_update_skill(skill_env):
    manifest.add_skill("up", {"slug": "up", "commit": "aaa"})
    assert manifest.update_skill("up", {"commit": "bbb"}) is True
    skill = manifest.get_skill("up")
    assert skill["commit"] == "bbb"


def test_update_nonexistent(skill_env):
    assert manifest.update_skill("ghost", {"commit": "x"}) is False


def test_is_installed(skill_env):
    manifest.add_skill("exists", {"slug": "exists"})
    assert manifest.is_installed("exists") is True
    assert manifest.is_installed("nope") is False
