# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.0.1] — 2026-06-03

### Changed — README reflects the v1.0 runtime-agnostic architecture

- Rewrote the intro (no longer "a Claude Code plugin" only) and added a **Runtime support**
  section documenting the capability ladder, adapters, neutral entrypoints, and the canonical
  spec files. Points to ADR-001. Docs-only; no behavior change.

## [1.0.0] — 2026-06-03

### Added — runtime-agnostic spec + adapters (ADR-001 implementation, v1.0)

Implements ADR-001 (§10 phased rollout). The bootstrap pattern is no longer Claude-only: a
single runtime-neutral `persona.yaml` hydrates working personas on any runtime, at the highest
fidelity that runtime supports. Every capability verb and schema field was coined during real
adapter work and exercised on a real dogfood project (55%→100% coverage) — nothing speculative
(YAGNI).

- **Neutral entrypoints** in `assets/collab-repo/`:
  - `START.md` — front door; routes on directory state + documents runtime keys (§7.3).
  - `ORCHESTRATE.md` — Role 1 (bootstrap a new project), runtime-neutral.
  - `PARTICIPATE.md` — Role 2 (join a project) + the 3-tier capability ladder.
- **Adapters** in `assets/collab-repo/adapters/<runtime>/HYDRATE.md` (the only runtime-specific
  surface; Open/Closed for runtimes):
  - `generic/` — Tier-1 fallback (MANDATORY): re-read `persona.yaml` each turn, self-enforce.
  - `code-puppy/` — Tier-3: maps capabilities to enforced JSON sub-agent tool allow-lists.
  - `claude/` — Tier-2: renders `persona.yaml` → `CLAUDE.md` + `/vc`, mirroring v0.3.x shape.
- **Canonical spec docs** in `references/`: `capability-vocab.v1.md` (frozen 10-verb API),
  `persona.schema.md`, `manifest.schema.md` (relative paths + configurable backlog source).
- **`agents/__DEV__/persona.yaml`** — machine-truth companion to the existing `__DEV__/AGENT.md`
  (yaml canonical, md derived).
- **`tests/bi_runtime_accept.py`** — bi-runtime acceptance harness: proves one `persona.yaml`
  yields an identical behavior contract (identity, capabilities, guardrails) on code-puppy +
  Claude. Passes for both a `dev` and a read-only `reviewer` persona.

### Compatibility

- Purely additive. Existing v0.3.x scaffolds and invocations are unaffected.
- Claude native sub-agents (Tier-3 at home) deferred to a follow-up (ADR §10.8).

### Changed — de-Claude the emitted `CONVENTIONS.md` (ADR §10.6)

- Replaced the "Tool hierarchy" section's runtime tool names (`Read`/`Write`/`Edit`/`Bash`,
  `gh` CLI) and the Obsidian/MCP note with capability-level language + a pointer to
  `adapters/<runtime>/HYDRATE.md` and `references/capability-vocab.v1.md`. The emitted
  convention doc is now runtime-neutral, matching the canon. Additive/cosmetic for existing
  scaffolds (no behavior change).

## [0.3.2] — 2026-05-29

Same-day follow-up to v0.3.1, closing out the remaining items from [Decision 6](https://github.com/vggg/Irisidian/blob/main/projects/multi-agent-setup/decisions/2026-05-29-6-bootstrap-genesis-emission.md). All v0.3.1 invocations still work unchanged.

### Added — runtime-aware cron + FAILOVER templating

- **`runtime:` taxonomy** for AGENT.md frontmatter, replacing the older `schedule-skill` / `github-actions` strings. Supported values:
  - `launchd-cron` — macOS launchd; per-runner machine; laptop must be on.
  - `systemd-timer` — Linux systemd timer; per-runner machine; laptop must be on.
  - `cloud-routine` — Anthropic-hosted `/schedule` routine; always-on.
  - `gh-actions-cron` — GitHub Actions scheduled workflow; always-on.
  - `gh-actions-event` — GitHub Actions on PR / event webhook (for `__AUTONOMOUS_EVENT__` personas).
  Each AGENT.md template now carries a comment block documenting the taxonomy inline.
- **Per-runtime FAILOVER cron section snippets** under `assets/collab-repo/_failover-cron-sections/`:
  - `launchd-cron.md` — generated wrapper + plist; `launchctl bootstrap` / `bootout` commands.
  - `systemd-timer.md` — generated `.service` + `.timer`; `systemctl --user` lifecycle.
  - `cloud-routine.md` — `/schedule` invocation; per-account billing notes.
  - `gh-actions-cron.md` — workflow file pattern; PAT secret requirements.
  The skill picks the right snippet at scaffold time based on the persona's `runtime:` field and substitutes it into the templated `agents/<persona>/FAILOVER.md`'s `{{FAILOVER_CRON_SECTION}}` placeholder.
- **`workspace-template/setup.sh` gains opt-in cron stub generation** behind `REGISTER_CRON=yes`:
  - `launchd-cron` → generates `~/Workspace/<project>/<persona>/com.<project>.<persona>.plist` + wrapper script. Stub is generated, NOT loaded; you load it manually via `launchctl bootstrap` after reviewing the schedule. Idempotent (skips if plist already exists).
  - `systemd-timer` → generates `.service` + `.timer` + wrapper. Same opt-in-load pattern.
  - `cloud-routine` → prints the `/schedule` command to run in Claude Code.
  - `gh-actions-*` → no-op locally (cron lives in the code repo workflow).
  Generation happens only when `REGISTER_CRON=yes` is set; default behavior is workspace-only.

### Changed

- **`agents/librarian/FAILOVER.md`** "Enable the cron on your machine" section is now `{{FAILOVER_CRON_SECTION}}` (per-runtime). The skill fills it from the matching `_failover-cron-sections/*.md` snippet.
- **`agents/__AUTONOMOUS_EVENT__/AGENT.md`** frontmatter `runtime` field is now `gh-actions-event` (was `github-actions`).

### Compatibility

- v0.3.1 invocations work unchanged. Existing collab repos do not need to migrate.
- The old `runtime: schedule-skill` and `runtime: github-actions` values still parse — the new taxonomy is additive.

### Why generation but not auto-load

Cron registration is the kind of action where "almost right" is much worse than "explicitly opt-in." DST drift, double-registration across two laptops, accidental cron-from-the-wrong-runner — these are real failure modes. The stub-and-load split makes the dangerous step explicit and human-reviewed. Auto-load may land in a later release once we've gathered usage data on whether the explicit step actually catches errors in practice.

### Validated against

VANAR's launchd-cron pilot (Vikram's machine, daily 15:00 PT). The generated plist + wrapper produced by v0.3.2's `setup.sh REGISTER_CRON=yes` matches VANAR's hand-rolled artifacts byte-for-byte (modulo the manual TODO timestamp adjustment).

## [0.3.1] — 2026-05-29

Patch release codifying lessons from VANAR's pilot day (first real use of v0.3.0). All additions are template content; no interface changes. v0.3.0 invocations still work unchanged.

### Added — `collab-repo-project` mode emissions

- **`QUICKSTART.md`** — agent-led onboarding doc as a first-class artifact. Contains the canonical "Onboard me to {{PROJECT_NAME}}" prompt that human collaborators paste into Claude Code / code-puppy / their AI coding agent. ~30 min to first PR vs. ~45 min for the manual BOOTSTRAP.md path.
- **`wiki/log.md`** — genesis log entry seeded at scaffold time. Establishes the `find -newer wiki/log.md` timestamp baseline so the Librarian's first cron run isn't a silent no-op.
- **`wiki/index.md`** — standard catalog scaffold (log, entities, concepts, sources sections with placeholder descriptions).
- **`_handoff/{{DATE}}-bootstrap-to-librarian-genesis.md`** — one-time genesis handoff for the Librarian. Acknowledges the wiki has been seeded; first run flips it to `status: done` and the standard cycle takes over.
- **`workspace-template/{CLAUDE.md, AGENTS.md, setup.sh}`** — runtime-portable workspace bootstrap. `setup.sh <persona-slug>` clones both repos into `~/Workspace/{{PROJECT_NAME}}/<slug>/`, configures per-repo git identity, and drops the thin CLAUDE.md (Claude Code) + AGENTS.md (code-puppy and similar) pointers. Cron self-registration deferred to v0.4.0.

### Added — template content updates

- **CONVENTIONS.md `_handoff/` lifecycle:** new "Push policy" paragraph carving out `_handoff/` files as direct-push-permitted on `main` (they're coordination metadata, not substantive changes). Resolves a doc-fork that surfaced when persona AGENT.md "PR only" rules clashed with BOOTSTRAP "push origin main" guidance for the joined handoff.
- **BOOTSTRAP.md Step 3 (rewritten):** consolidated "fire up your VANAR workspace" with the new `~/Workspace/{{PROJECT_NAME}}/<your-slug>/` folder pattern (both repos in one folder) + an optional AI-agent bootstrap sub-section (CLAUDE.md / AGENTS.md template for Claude Code / code-puppy users).
- **BOOTSTRAP.md Step 6 (new):** "Announce yourself to the Librarian" — the joined collaborator drops a `_handoff/` so the Librarian picks them up on the next run and updates the wiki personas page.
- **Root `CLAUDE.md`:** `QUICKSTART.md` promoted to item 1 in "Read these first" (fast path); `BOOTSTRAP.md` becomes item 2 (deeper reference).
- **`agents/__DEV__/AGENT.md`:** optional two-clone note for project owner — owners often have a "library copy" clone (used by their personal Iris) separate from their dev working copy. Conditionally rendered.
- **`agents/__AUTONOMOUS_CRON__/AGENT.md`** + **`agents/__AUTONOMOUS_EVENT__/AGENT.md`:** new "First-run handling" section telling the persona to look for and process a `_handoff/*-bootstrap-to-*-genesis.md` file before its standard cycle.
- **`agents/librarian/AGENT.md`:** new "Drift checks" section listing concrete things to compare across files (AGENT.md frontmatter `runtime:` vs FAILOVER.md cron section; AGENT.md scope vs CONVENTIONS routing table; AGENT.md cadence vs actual cron file). Librarian surfaces drift; never auto-fixes.

### Compatibility

- v0.3.0 invocations work without changes. Existing collab repos do not need to migrate; v0.3.1 only affects new scaffolds.
- The `mode:collab-repo-project` artifact set is now ~24 files (was 20 in v0.3.0).

### Validated against

VANAR (first project to use the collab-repo-project mode). All v0.3.1 additions were hand-rolled into VANAR's collab repo during 2026-05-29 and validated by the Librarian (Vidya) successfully processing the manual genesis handoff and surfacing drift on her first scheduled cron run.

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
