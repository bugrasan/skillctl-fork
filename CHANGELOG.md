# Changelog

## 0.1.0 (2026-03-16)

Initial release.

### Commands (12)

- `search` — find skills in registries and locally with scored ranking
- `install` — clone from GitHub + symlink into skills dir
- `list` — show installed skills with timestamps
- `create` — scaffold a new skill from template
- `update` — pull latest for git-installed skills
- `remove` — uninstall with reference-counted clones
- `info` — skill details (local or GitHub)
- `config` — view/set configuration
- `registry` — add, remove, list, reset trusted registries
- `schema` — dump CLI schema for agent self-discovery
- `learn` — interactive guide to writing skills (anatomy, write, organize, examples)
- `lint` — score and validate a skill against best practices (0-100)

### Features

- **Registry-first discovery**: searches `anthropics/skills` and `vercel-labs/agent-skills` by default
- **Custom registries**: `skillctl registry add myorg/skills` with validation
- **LLM-enriched search**: generates keywords, short descriptions, and categories via Claude Haiku or GPT-5 mini
- **SHA-based incremental cache**: only re-enriches skills whose content changed
- **Three-layer search**: synonyms + scored ranking + LLM keywords
- **Agent-friendly JSON**: `--json` on every command with `next_actions`, `--fields` mask, `--quiet` mode
- **Monorepo support**: `--path` flag for installing skills from subdirectories
- **Reference-counted clones**: shared monorepo clones preserved when removing one skill
- **Input validation**: regex patterns on repo/slug, `expected_pattern` in JSON errors
- **Design system**: semantic Rich theme, custom renderables, Calvin S ASCII logo
- **First-run onboarding**: interactive setup with sensible defaults
- **Lazy imports**: fast startup (~120ms for non-network commands)
- **118 tests passing**
