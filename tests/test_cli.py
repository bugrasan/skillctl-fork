"""Tests for CLI commands using Typer's test runner."""

import json

from typer.testing import CliRunner

from skillctl.cli import app
from skillctl import manifest

runner = CliRunner()


class TestRootCommand:
    def test_no_args_shows_welcome(self, skill_env):
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "skillctl" in result.output
        assert "search" in result.output
        assert "install" in result.output

    def test_version(self, skill_env):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestSchema:
    def test_schema_returns_json(self, skill_env):
        result = runner.invoke(app, ["schema"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "skillctl"
        assert data["version"] == "0.1.0"
        assert "commands" in data
        assert "exit_codes" in data

    def test_schema_has_all_commands(self, skill_env):
        result = runner.invoke(app, ["schema"])
        data = json.loads(result.output)
        commands = data["commands"]
        for cmd in ["search", "install", "list", "create", "update", "remove", "info", "config", "schema"]:
            assert cmd in commands, f"Missing command: {cmd}"

    def test_schema_has_patterns(self, skill_env):
        result = runner.invoke(app, ["schema"])
        data = json.loads(result.output)
        # install repo arg has a pattern
        assert "pattern" in data["commands"]["install"]["args"]["repo"]
        # create slug arg has a pattern
        assert "pattern" in data["commands"]["create"]["args"]["slug"]


class TestSearch:
    def test_search_local(self, skill_env):
        # Create a skill first so there's something to find
        runner.invoke(
            app,
            ["create", "pdf-tool", "--name", "PDF Tool", "--desc", "Process PDFs", "-y"],
        )
        result = runner.invoke(app, ["search", "pdf", "--source=local"])
        assert result.exit_code == 0
        assert "pdf-tool" in result.output.lower() or "PDF Tool" in result.output

    def test_search_no_results(self, skill_env):
        result = runner.invoke(
            app, ["search", "xyznonexistent999", "--source=local"]
        )
        assert result.exit_code == 2
        assert "No skills found" in result.output

    def test_search_json(self, skill_env):
        runner.invoke(
            app,
            ["create", "test-s", "--name", "Test S", "--desc", "test search", "-y"],
        )
        result = runner.invoke(
            app, ["search", "test", "--source=local", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        results = data.get("results", data)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert "next_actions" in data

    def test_search_limit(self, skill_env):
        # Create 3 skills
        for i in range(3):
            runner.invoke(
                app,
                ["create", f"skill-{i}", "--name", f"Skill {i}", "--desc", "test", "-y"],
            )
        result = runner.invoke(
            app, ["search", "skill", "--source=local", "--json", "--limit", "2"]
        )
        data = json.loads(result.output)
        results = data.get("results", data)
        assert len(results) == 2

    def test_search_offset(self, skill_env):
        for i in range(3):
            runner.invoke(
                app,
                ["create", f"sk-{i}", "--name", f"SK {i}", "--desc", "test", "-y"],
            )
        result = runner.invoke(
            app, ["search", "sk", "--source=local", "--json", "--offset", "1"]
        )
        data = json.loads(result.output)
        results = data.get("results", data)
        assert len(results) == 2  # 3 total - 1 offset = 2

    def test_search_fields(self, skill_env):
        runner.invoke(
            app,
            ["create", "fs", "--name", "FS", "--desc", "field test", "-y"],
        )
        result = runner.invoke(
            app, ["search", "field", "--source=local", "--json", "--fields", "slug,installed"]
        )
        data = json.loads(result.output)
        results = data.get("results", data)
        assert len(results) >= 1
        assert "slug" in results[0]
        assert "description" not in results[0]


class TestCreate:
    def test_create_non_interactive(self, skill_env):
        result = runner.invoke(
            app,
            [
                "create", "test-skill",
                "--name", "Test Skill",
                "--desc", "A test",
                "--tags", "a,b",
                "--author", "me",
                "-y",
            ],
        )
        assert result.exit_code == 0
        assert "Created" in result.output
        assert manifest.is_installed("test-skill")

    def test_create_json(self, skill_env):
        result = runner.invoke(
            app,
            [
                "create", "json-skill",
                "--name", "JSON Skill",
                "-y", "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "created"
        assert data["slug"] == "json-skill"
        assert "next_actions" in data

    def test_create_invalid_slug(self, skill_env):
        result = runner.invoke(
            app,
            ["create", "bad slug!", "-y"],
        )
        assert result.exit_code == 2

    def test_create_invalid_slug_json_has_pattern(self, skill_env):
        result = runner.invoke(
            app,
            ["create", "bad slug!", "-y", "--json"],
        )
        assert result.exit_code == 2
        data = json.loads(result.output)
        assert "expected_pattern" in data

    def test_create_duplicate(self, skill_env):
        runner.invoke(
            app,
            ["create", "dup-skill", "--name", "Dup", "-y"],
        )
        result = runner.invoke(
            app,
            ["create", "dup-skill", "--name", "Dup2", "-y"],
        )
        assert result.exit_code == 1


class TestList:
    def test_list_empty(self, skill_env):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No skills installed" in result.output

    def test_list_with_skills(self, skill_env):
        runner.invoke(
            app,
            ["create", "s1", "--name", "S1", "-y"],
        )
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "s1" in result.output

    def test_list_shows_installed_column(self, skill_env):
        runner.invoke(
            app,
            ["create", "ts", "--name", "TS", "-y"],
        )
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Installed" in result.output

    def test_list_json(self, skill_env):
        runner.invoke(
            app,
            ["create", "s1", "--name", "S1", "-y"],
        )
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        results = data.get("results", data)
        if isinstance(results, list):
            assert len(results) >= 1

    def test_list_json_fields(self, skill_env):
        runner.invoke(
            app,
            ["create", "s1", "--name", "S1", "-y"],
        )
        result = runner.invoke(
            app, ["list", "--json", "--fields", "slug,source"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        results = data.get("results", data)
        if isinstance(results, list) and results:
            item = results[0]
            assert "slug" in item
            assert "name" not in item

    def test_list_quiet(self, skill_env):
        runner.invoke(app, ["create", "a1", "--name", "A1", "-y"])
        runner.invoke(app, ["create", "b2", "--name", "B2", "-y"])
        result = runner.invoke(app, ["list", "--quiet"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        slugs = {line.strip() for line in lines}
        assert "a1" in slugs
        assert "b2" in slugs
        # quiet mode should NOT have table headers
        assert "Source" not in result.output


class TestInfo:
    def test_info_installed(self, skill_env):
        runner.invoke(
            app,
            ["create", "my-info", "--name", "Info Skill", "-y"],
        )
        result = runner.invoke(app, ["info", "my-info"])
        assert result.exit_code == 0
        assert "Info Skill" in result.output
        assert "installed" in result.output

    def test_info_json(self, skill_env):
        runner.invoke(
            app,
            [
                "create", "j-info",
                "--name", "JSON Info",
                "--desc", "test",
                "-y",
            ],
        )
        result = runner.invoke(app, ["info", "j-info", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "JSON Info"
        assert "next_actions" in data

    def test_info_not_found(self, skill_env):
        result = runner.invoke(app, ["info", "ghost"])
        assert result.exit_code == 2


class TestRemove:
    def test_remove_with_yes(self, skill_env):
        runner.invoke(
            app,
            ["create", "removeme", "--name", "RM", "-y"],
        )
        assert manifest.is_installed("removeme")

        result = runner.invoke(
            app, ["remove", "removeme", "-y"]
        )
        assert result.exit_code == 0
        assert "Removed" in result.output
        assert not manifest.is_installed("removeme")

    def test_remove_json(self, skill_env):
        runner.invoke(
            app,
            ["create", "rm-json", "--name", "RM", "-y"],
        )
        result = runner.invoke(
            app, ["remove", "rm-json", "-y", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "removed"

    def test_remove_not_found(self, skill_env):
        result = runner.invoke(
            app, ["remove", "ghost", "-y"]
        )
        assert result.exit_code == 2

    def test_remove_dry_run(self, skill_env):
        runner.invoke(
            app,
            ["create", "dr-skill", "--name", "DR", "-y"],
        )
        result = runner.invoke(
            app, ["remove", "dr-skill", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert manifest.is_installed("dr-skill")  # still exists

    def test_remove_shared_clone_kept(self, skill_env):
        """When two skills share a clone, removing one keeps the clone."""
        clone_path = str(skill_env["repos_dir"] / "org__monorepo")
        # Simulate two skills from same monorepo
        manifest.add_skill("skill-a", {
            "slug": "skill-a",
            "source": "github",
            "repo": "org/monorepo",
            "path": str(skill_env["skills_dir"] / "skill-a"),
            "clone_path": clone_path,
            "sub_path": "skills/a",
        })
        manifest.add_skill("skill-b", {
            "slug": "skill-b",
            "source": "github",
            "repo": "org/monorepo",
            "path": str(skill_env["skills_dir"] / "skill-b"),
            "clone_path": clone_path,
            "sub_path": "skills/b",
        })

        result = runner.invoke(
            app, ["remove", "skill-a", "-y", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["clone_kept"] is True
        assert "skill-b" in data["reason"]
        assert manifest.is_installed("skill-b")
        assert not manifest.is_installed("skill-a")

    def test_remove_multiple_with_yes(self, skill_env):
        """Batch remove: remove 3 skills at once."""
        for name in ("rm-a", "rm-b", "rm-c"):
            runner.invoke(
                app, ["create", name, "--name", name.upper(), "-y"]
            )
            assert manifest.is_installed(name)

        result = runner.invoke(
            app, ["remove", "rm-a", "rm-b", "rm-c", "-y"]
        )
        assert result.exit_code == 0
        for name in ("rm-a", "rm-b", "rm-c"):
            assert not manifest.is_installed(name)

    def test_remove_multiple_json(self, skill_env):
        """Batch remove JSON output uses results array."""
        for name in ("mj-a", "mj-b"):
            runner.invoke(
                app, ["create", name, "--name", name.upper(), "-y"]
            )

        result = runner.invoke(
            app, ["remove", "mj-a", "mj-b", "-y", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert len(data["results"]) == 2
        assert all(r["status"] == "removed" for r in data["results"])

    def test_remove_single_json_backward_compat(self, skill_env):
        """Single-skill remove JSON keeps flat object (no results array)."""
        runner.invoke(
            app, ["create", "bc-skill", "--name", "BC", "-y"]
        )
        result = runner.invoke(
            app, ["remove", "bc-skill", "-y", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "removed"
        assert "results" not in data

    def test_remove_multiple_partial_not_found(self, skill_env):
        """Batch remove: 1 of 3 not found → skip, exit 1."""
        runner.invoke(
            app, ["create", "pf-a", "--name", "PF", "-y"]
        )
        runner.invoke(
            app, ["create", "pf-b", "--name", "PF", "-y"]
        )

        result = runner.invoke(
            app, ["remove", "pf-a", "ghost", "pf-b", "-y"]
        )
        assert result.exit_code == 1
        assert not manifest.is_installed("pf-a")
        assert not manifest.is_installed("pf-b")

    def test_remove_multiple_shared_clone(self, skill_env):
        """Batch remove: 2 skills from same clone — clone deleted after last."""
        clone_dir = skill_env["repos_dir"] / "org__monorepo"
        clone_dir.mkdir(parents=True)
        clone_path = str(clone_dir)

        manifest.add_skill("mc-a", {
            "slug": "mc-a",
            "source": "github",
            "repo": "org/monorepo",
            "path": str(skill_env["skills_dir"] / "mc-a"),
            "clone_path": clone_path,
            "sub_path": "skills/a",
        })
        manifest.add_skill("mc-b", {
            "slug": "mc-b",
            "source": "github",
            "repo": "org/monorepo",
            "path": str(skill_env["skills_dir"] / "mc-b"),
            "clone_path": clone_path,
            "sub_path": "skills/b",
        })

        result = runner.invoke(
            app, ["remove", "mc-a", "mc-b", "-y", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["results"]) == 2
        # First removal keeps clone (mc-b still exists at that point)
        assert data["results"][0]["clone_kept"] is True
        # Second removal deletes clone (no siblings left)
        assert "clone_kept" not in data["results"][1]
        assert not manifest.is_installed("mc-a")
        assert not manifest.is_installed("mc-b")

    def test_remove_deduplicates_names(self, skill_env):
        """Duplicate names are deduplicated."""
        runner.invoke(
            app, ["create", "dup-skill", "--name", "DUP", "-y"]
        )

        result = runner.invoke(
            app, ["remove", "dup-skill", "dup-skill", "-y"]
        )
        # Second occurrence is deduplicated, so only one removal
        assert result.exit_code == 0
        assert not manifest.is_installed("dup-skill")


class TestInstall:
    def test_install_invalid_repo_format(self, skill_env):
        result = runner.invoke(
            app, ["install", "not-a-repo-format", "-y"]
        )
        assert result.exit_code == 2

    def test_install_invalid_repo_json_has_pattern(self, skill_env):
        result = runner.invoke(
            app, ["install", "../../etc/passwd", "-y", "--json"]
        )
        assert result.exit_code == 2
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert data["code"] == 2
        assert "expected_pattern" in data

    def test_install_dry_run(self, skill_env):
        result = runner.invoke(
            app,
            ["install", "user/repo", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_install_dry_run_json(self, skill_env):
        result = runner.invoke(
            app,
            ["install", "user/repo", "--dry-run", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert len(data["actions"]) == 3

    def test_install_multi_path_dry_run(self, skill_env):
        """Multi-path dry-run lists actions for all paths."""
        result = runner.invoke(
            app,
            [
                "install", "user/monorepo", "--dry-run",
                "--path", "skills/a",
                "--path", "skills/b",
            ],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_install_multi_path_dry_run_json(self, skill_env):
        """Multi-path dry-run JSON has clone + symlink actions for each path."""
        result = runner.invoke(
            app,
            [
                "install", "user/monorepo", "--dry-run", "--json",
                "--path", "skills/a",
                "--path", "skills/b",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        # 1 clone + 2 symlinks + 2 registers = 5 actions
        assert len(data["actions"]) == 5
        assert data["actions"][0]["action"] == "clone"
        symlink_actions = [a for a in data["actions"] if a["action"] == "symlink"]
        assert len(symlink_actions) == 2

    def test_install_multi_path_slug_collision(self, skill_env):
        """Multi-path with duplicate slugs is rejected up-front."""
        result = runner.invoke(
            app,
            [
                "install", "user/monorepo", "--dry-run",
                "--path", "skills/a/utils",
                "--path", "services/b/utils",
            ],
        )
        assert result.exit_code == 2

    def test_install_single_path_backward_compat(self, skill_env):
        """Single --path dry-run still produces 3 actions (same as before)."""
        result = runner.invoke(
            app,
            ["install", "user/repo", "--dry-run", "--json", "--path", "skills/a"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert len(data["actions"]) == 3


class TestUpdate:
    def test_update_no_args(self, skill_env):
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 2

    def test_update_not_found(self, skill_env):
        result = runner.invoke(app, ["update", "ghost"])
        assert result.exit_code == 2


class TestConfig:
    def test_config_show(self, skill_env):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "skills_dir" in result.output
        assert "repos_dir" in result.output

    def test_config_set(self, skill_env):
        result = runner.invoke(
            app, ["config", "set", "cache_ttl", "7200"]
        )
        assert result.exit_code == 0

    def test_config_get(self, skill_env):
        result = runner.invoke(
            app, ["config", "get", "default_format"]
        )
        assert result.exit_code == 0
        assert "table" in result.output

    def test_config_set_invalid_key(self, skill_env):
        result = runner.invoke(
            app, ["config", "set", "bad_key", "value"]
        )
        assert result.exit_code == 2

    def test_config_get_invalid_key(self, skill_env):
        result = runner.invoke(
            app, ["config", "get", "bad_key"]
        )
        assert result.exit_code == 2
