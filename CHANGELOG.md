# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.3.0] — 2026-05-29

### Added

- **Multi-mode dispatch.** SKILL.md restructured around three modes selected at invocation:
  - `vault-project` — original v0.2.0 behaviour (vault-based five-agent project scaffold), preserved verbatim.
  - `collab-repo-project` — emits a dedicated collab repo for projects with remote collaborators. Implements the "Option A" pattern: collab substrate (conventions, coordination, agent manuals, handoffs, decisions, findings, project wiki) lives in its own GitHub repo, separable from any personal vault.
  - `join-collab-project` — walks a human remote collaborator through cloning an existing collab repo, claiming a persona, setting per-repo git identity, and validating the round trip with a "hello" PR.
- **`assets/collab-repo/` template tree** (16 new files) for the `collab-repo-project` mode:
  - Root: `README.md`, `CONVENTIONS.md`, `COORDINATION.md` (with `## Hot files` section), `CLAUDE.md`, `BOOTSTRAP.md` (collaborator-facing), `BOOTSTRAP-ADMIN.md` (owner-only operations including optional trust-gating).
  - `agents/__DEV__/AGENT.md` — human dev persona template (workspace path, session-start ritual, ADR rules).
  - `agents/__AUTONOMOUS_EVENT__/AGENT.md` — webhook-triggered autonomous persona template (e.g. PR Reviewer, Backtest Runner). Cost ceilings, decision authority, hot-file flagging.
  - `agents/__AUTONOMOUS_CRON__/AGENT.md` — `/schedule`-triggered autonomous persona template (e.g. PM+UAT). Cadence, default runner, failover.
  - `agents/librarian/AGENT.md` + `agents/librarian/FAILOVER.md` — always emitted by default; centralized-with-failover model documented.
  - Subfolder stubs with READMEs: `_handoff/`, `decisions/`, `findings/`, `wiki/`.
- **New reference doc:** `references/collab-repo-design.md` — rationale for the collab-repo-project mode design choices (why a separate repo, why three persona archetypes, why centralized-with-failover librarian, why optional trust-gating, etc.).

### Changed

- `SKILL.md` is no longer a single emit sequence. It's now a dispatcher that documents mode selection, then provides three self-contained mode-specific emit sections. The `vault-project` section preserves v0.2.0 behaviour unchanged — existing usage is unaffected.
- File manifest updated to reflect the new asset tree.

### Compatibility

- v0.2.0 invocations (vault-project mode) work without changes. Existing users do not need to migrate.
- The `mode:` parameter is the new entry point. If unspecified, the skill prompts for mode selection.

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
