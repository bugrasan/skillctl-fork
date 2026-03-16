"""Tests for config management."""

from unittest.mock import patch

import yaml

from skillctl.config import load_config, save_config, set_config_value


def test_load_defaults(skill_env):
    config = load_config()
    assert config.skills_dir == str(skill_env["skills_dir"])
    assert config.repos_dir == str(skill_env["repos_dir"])
    assert config.scan_paths == []
    assert config.default_format == "table"
    assert config.cache_ttl == 3600


def test_save_and_reload(skill_env):
    config = load_config()
    config.skills_dir = "/custom/skills"
    config.scan_paths = ["/extra/path"]
    save_config(config)

    reloaded = load_config()
    assert reloaded.skills_dir == "/custom/skills"
    assert reloaded.scan_paths == ["/extra/path"]


def test_set_config_value(skill_env):
    set_config_value("skills_dir", "/new/skills")
    config = load_config()
    assert config.skills_dir == "/new/skills"


def test_set_scan_paths_comma_separated(skill_env):
    set_config_value("scan_paths", "/a, /b, /c")
    config = load_config()
    assert config.scan_paths == ["/a", "/b", "/c"]


def test_set_invalid_key(skill_env):
    import pytest

    with pytest.raises(ValueError, match="Unknown config key"):
        set_config_value("nonexistent_key", "value")


def test_set_invalid_format(skill_env):
    import pytest

    with pytest.raises(ValueError, match="Invalid format"):
        set_config_value("default_format", "xml")


def test_gh_token_autodetect(skill_env):
    with patch(
        "skillctl.config._detect_gh_token", return_value="gh-token-123"
    ):
        config = load_config()
        assert config.github_token == "gh-token-123"


def test_gh_token_not_persisted_on_save(skill_env):
    with patch(
        "skillctl.config._detect_gh_token", return_value="gh-token-123"
    ):
        config = load_config()
        save_config(config)

    # Read raw file — token should not be there
    with open(skill_env["config_path"]) as f:
        data = yaml.safe_load(f)
    assert "github_token" not in data


def test_skills_path_property(skill_env):
    config = load_config()
    assert config.skills_path == skill_env["skills_dir"]
    assert config.repos_path == skill_env["repos_dir"]
