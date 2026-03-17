<div align="center">

<h1>skill<em>ctl</em></h1>

<p><strong>The package manager for agent skills.</strong></p>

<p>Search, install, and manage SKILL.md files.<br>
Stateless, zero-config, and token-efficient.</p>

[![PyPI](https://img.shields.io/pypi/v/skillctl)](https://pypi.org/project/skillctl/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/skillctl)](https://pypi.org/project/skillctl/)
[![License: MIT](https://img.shields.io/pypi/l/skillctl)](LICENSE)
[![CI](https://github.com/dvlshah/skillctl/actions/workflows/ci.yml/badge.svg)](https://github.com/dvlshah/skillctl/actions/workflows/ci.yml)

</div>

<br>

- [x] **Zero tokens when idle** — stateless CLI, no server process, no protocol overhead
- [x] **One command to install** — `git clone` → symlink → registered, done in seconds
- [x] **Agent-native** — every command supports `--json` with `next_actions` guidance
- [x] **Works today** — Claude Code, Codex, and any agent that reads markdown

<br>

## Quickstart (2 min)

### 1. Install

```
pip install skillctl
```

### 2. Find a skill

```bash
$ skillctl search "pdf"

  ●  pdf               registry  Create, edit, and extract content from PDFs   ★ 0
  ○  pdf-to-markdown   github    Convert PDF files to clean markdown           ★ 89
  ○  pdf-ocr           github    OCR extraction from scanned PDFs              ★ 67
```

### 3. Install it

```bash
$ skillctl install anthropics/skills --path skills/pdf

  ✓ Cloned anthropics/skills → ~/.skillctl/repos/anthropics__skills
  ✓ Linked → ~/.claude/skills/pdf
  ✓ Registered in manifest
```

Your agent picks it up immediately — no restart, no config change.

<br>

## The problem

Every AI agent runtime uses skills — markdown files that define what an agent can do. But skills live scattered across GitHub repos, local folders, and team drives. Developers copy-paste skill files manually and hope they work.

There's no `npm install` for skills.

## The solution

skillctl is a package manager purpose-built for agent skills.

```
skillctl search "excel"  →  finds xlsx skill (via LLM-enriched keywords)
skillctl install ...      →  git clone → symlink → registered
~/.claude/skills/xlsx/    →  agent picks it up automatically
```

<br>

## Using with coding agents

skillctl installs skills as symlinks into directories your agent already reads. No plugin, no integration, no restart.

**Claude Code**

```bash
skillctl config set skills_dir ~/.claude/skills    # default — already set
skillctl install anthropics/skills --path skills/pdf
# Claude Code picks it up on the next message — the /pdf skill appears automatically
```

**OpenAI Codex**

```bash
skillctl config set skills_dir ~/.codex/skills
skillctl install anthropics/skills --path skills/pdf
# Codex reads the skills directory on session start
```

**Any agent with bash access** can use skillctl directly — the CLI follows the same `search → install → use` pattern agents know from `pip`, `npm`, and `gh`:

```bash
# An agent can do this autonomously:
skillctl search "data analysis" --json --fields=slug,installed
skillctl install anthropics/skills --path skills/xlsx -y --json
cat ~/.claude/skills/xlsx/SKILL.md   # agent reads and follows the instructions
```

> [!NOTE]
> skillctl is designed **agent-first**. Every command supports `--json` with guided `next_actions`, `--quiet` for piping, `--yes` to skip prompts, and `skillctl schema` for runtime self-discovery. Agents don't need documentation — they can introspect the CLI.

<br>

## Why CLI, not MCP

Most agent tooling burns tokens while idle. skillctl costs zero.

| | CLI (skillctl) | MCP Server |
|---|---|---|
| **Tokens when idle** | 0 | Constant |
| **Setup** | `pip install` | Config, auth, daemon |
| **Agent compatibility** | Every LLM knows CLI | Protocol-specific |
| **Statefulness** | Stateless | Stateful process |

<br>

## Commands

<details open>
<summary><strong>Find & install</strong></summary>

```bash
skillctl search "pdf"                         # Search registries + local
skillctl search "pdf" --source=github         # Broad GitHub search
skillctl install user/repo                    # Full repo as a skill
skillctl install user/repo --path skills/pdf  # Subdirectory from monorepo
skillctl install user/repo --dry-run          # Preview without executing
```

</details>

<details open>
<summary><strong>Manage</strong></summary>

```bash
skillctl list                                 # Show installed skills
skillctl list --quiet                         # Bare names (for piping)
skillctl info my-skill                        # Detailed skill card
skillctl update my-skill                      # Pull latest from git
skillctl update --all                         # Update everything
skillctl remove my-skill                      # Uninstall (ref-counted clones)
```

</details>

<details open>
<summary><strong>Create & validate</strong></summary>

```bash
skillctl create my-skill --name "My Skill" --desc "Does X"
skillctl lint my-skill                        # Score 0-100 with fix suggestions
```

```
  my-skill                              Score: 65/100

  █████████████████████░░░░░░░░░  65%

  ✓ Has name, description, and tags in frontmatter
  ✓ Has 'When to Use' trigger section
  ✗ Missing anti-patterns section      +15 pts
  ✗ No code examples                   +20 pts
```

</details>

<details open>
<summary><strong>Learn</strong></summary>

```bash
skillctl learn                       # Topic index
skillctl learn anatomy               # The 5 layers of a great skill
skillctl learn write                 # Writing for AI comprehension
skillctl learn organize              # Directory structure & naming
skillctl learn examples              # Browse well-written reference skills
```

</details>

<details>
<summary><strong>Registries</strong></summary>

```bash
skillctl registry                    # List configured registries
skillctl registry add org/repo       # Add (validates skills exist)
skillctl registry remove org/repo
skillctl registry reset              # Reset to defaults
```

**Default registries (99 skills out of the box):**

| Registry | Skills | Description |
|----------|--------|-------------|
| [anthropics/skills](https://github.com/anthropics/skills) | 17 | Official Anthropic skills — PDF, XLSX, PPTX, frontend design, Claude API |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 5 | Vercel's React, Next.js, and deployment best practices |
| [tech-leads-club/agent-skills](https://github.com/tech-leads-club/agent-skills) | 77 | Curated registry — security, CI/CD, Docker, databases, and more |

Add your own with `skillctl registry add org/repo`

</details>

<details>
<summary><strong>Configuration</strong></summary>

```bash
skillctl config                              # Show current config
skillctl config set skills_dir ~/skills      # Change skills directory
skillctl config set registries "org/repo1,org/repo2"
```

</details>

<br>

## Agent mode

Every command supports `--json`. Responses include `next_actions` so agents can chain commands without hallucinating:

```bash
$ skillctl search "pdf" --json --fields=slug,installed
```

```json
{
  "results": [
    {"slug": "pdf", "installed": false},
    {"slug": "pdf-to-markdown", "installed": false}
  ],
  "next_actions": [
    "skillctl install anthropics/skills --path skills/pdf -y --json",
    "skillctl info pdf --json"
  ]
}
```

```bash
$ skillctl schema    # Full CLI introspection — agents discover commands at runtime
```

<br>

## How install works

```
skillctl install anthropics/skills --path skills/pdf
         │
         ├─ git clone → ~/.skillctl/repos/anthropics__skills/
         ├─ symlink   → ~/.claude/skills/pdf → (clone)/skills/pdf
         └─ register  → ~/.skillctl/manifest.json
```

- **Shared clones** — installing two skills from the same repo uses one clone
- **Ref-counted removal** — shared clones are kept until the last skill is removed
- **Atomic updates** — `git pull` on the clone updates all skills from that repo

<br>

## Search

Search uses a three-layer system:

1. **Synonym expansion** — "excel" finds `xlsx`, "figma" finds `frontend-design`
2. **Scored ranking** — slug > keywords > name > tags > description
3. **LLM enrichment** — generates search keywords at index time (optional, cached with SHA invalidation)

> [!NOTE]
> Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to enable LLM enrichment. Runs once per skill, costs ~$0.0005 each, cached with content-addressed SHA invalidation.

<br>

## SKILL.md format

Skills are markdown files with YAML frontmatter. Run `skillctl learn anatomy` for the full breakdown.

```yaml
---
name: sql-standards
description: SQL coding standards for our team
tags: [sql, standards]
---
```

```markdown
## When to Use This Skill
Use when the user asks to write or review SQL.

## Core Principles
- Always use UPPERCASE for SQL keywords
- Never use SELECT *

## Common Mistakes to Avoid
- ✗ SELECT * FROM users → ✓ SELECT id, name FROM users

## Examples
```

<br>

## Command reference

| Command | Description |
|---|---|
| `search` | Find skills across registries, GitHub, and local directories |
| `install` | Clone from GitHub + symlink into skills dir |
| `list` | Show installed skills with source and timestamps |
| `create` | Scaffold a new skill with SKILL.md template |
| `update` | Pull latest for git-installed skills |
| `remove` | Uninstall with reference-counted clones |
| `info` | Skill details — author, tags, source, path |
| `lint` | Score skill quality 0-100 with fix suggestions |
| `learn` | Interactive guide to writing great skills |
| `config` | View/set configuration |
| `registry` | Manage trusted skill registries |
| `schema` | Full CLI schema for agent self-discovery |

<br>

## Contributing

The easiest way to contribute is to pick an issue with the `good first issue` tag.

```bash
git clone https://github.com/dvlshah/skillctl.git
cd skillctl
pip install -e ".[dev]"
pytest
```

Bug report? [Open an issue](https://github.com/dvlshah/skillctl/issues). Feature request? [Open an issue](https://github.com/dvlshah/skillctl/issues).

<br>

> [!TIP]
> If skillctl saves you time, star the repo — it helps other developers find it.

<br>

## License

MIT
