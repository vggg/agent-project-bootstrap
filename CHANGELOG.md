# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] — 2026-05-27

### Added
- New asset: `assets/commands/vc.md` — the `/vc` slash command for vault commits. Installed to `~/.claude/commands/vc.md` (user-global), available to every Claude Code session. Workflow: check vault state, stage thoughtfully (never `git add -A`), compose a commit message using the canonical `<persona>: <operation> | <description>` convention, commit, push, and verify the push against GitHub. Uses `{{VAULT_PATH}}` placeholder; derives the vault GitHub repo from `git remote get-url origin` so no new placeholder is required.
- SKILL.md: new emit step `3a` documenting the commands copy step; file manifest updated.
- README.md: new "Slash commands" section under *What gets generated*.

## [0.1.1] — 2026-05-22

### Added
- Workspace context files: `CLAUDE.md` (repo orientation + sync rules), `CHANGELOG.md`, `CONTRIBUTING.md`.
- Sync rule documented: vault is canonical, this repo is a release snapshot.

## [0.1.0] — 2026-05-22

### Added
- Initial release of the `agent-project-bootstrap` skill.
- Vault scaffolding templates, workspace scaffolding templates, reference docs.
