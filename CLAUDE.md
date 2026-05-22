# agent-project-bootstrap — Repo Guide

## What this repo is

A **published release snapshot** of the `agent-project-bootstrap` Claude Code skill. The canonical working copy lives in a private Obsidian vault at `_meta/skills/agent-project-bootstrap/`. This repo is updated manually on each release.

## Sync rule

**Vault is canonical. This repo is read-only between releases.**

- Edit the skill in the vault, not here.
- On release: sync changed files from vault → `skills/agent-project-bootstrap/`, bump version in `.claude-plugin/plugin.json` and `CHANGELOG.md`, commit, tag, push, create GitHub release.
- Never edit `skills/` or `.claude-plugin/` directly in this repo. Only repo-meta files (`CLAUDE.md`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`) may be edited here between releases.

## Repo layout

```
.claude-plugin/
  plugin.json             # plugin manifest — version number lives here
skills/
  agent-project-bootstrap/
    SKILL.md              # Claude-facing emit instructions
    references/           # design rationale and setup guides
    assets/
      vault/              # vault file templates
      workspaces/         # workspace CLAUDE.md templates
CHANGELOG.md
CLAUDE.md                 # this file
CONTRIBUTING.md
LICENSE
README.md
```

## Versioning

Follows semver. Patch (0.0.x): wording fixes, typos, broken references. Minor (0.x.0): new placeholders, new template sections, structural improvements. Major (x.0.0): breaking changes to the emit process or file layout.

## Release workflow

```bash
# 1. Sync changed files from vault into skills/agent-project-bootstrap/
# 2. Bump version in .claude-plugin/plugin.json
# 3. Prepend entry to CHANGELOG.md
git add .
git commit -m "release: vX.Y.Z — <summary>"
git push
git tag -a vX.Y.Z -m "<summary>"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z — <summary>" --notes "<notes>"
```

## Testing

Install from a local clone:
```bash
/plugin install /path/to/agent-project-bootstrap
```
Invoke in a throwaway directory and verify the emitted files match the templates in `skills/agent-project-bootstrap/assets/`.

## What this repo is NOT

- Not a multi-agent project — no coordination protocol, no vault, no handoffs here
- Not a development surface — don't iterate on template content in this repo directly
- Not the canonical copy — edits made here without syncing back to the vault will be lost on next release
