# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added — `multi-agent-audit` skill + `project-auditor` subagent (sister skill to `agent-project-bootstrap`)

New skill at `skills/multi-agent-audit/` for grading multi-agent software projects against an evidence-based rubric. Sister to `agent-project-bootstrap`: bootstrap **builds** multi-agent projects; multi-agent-audit **grades** them. **Read-only by construction.** Headline metric: **INTERVENTION TAX** = human touches per autonomous task. Framework-neutral (works on `agent-project-bootstrap`, CrewAI, LangGraph, AutoGen, Copilot agents, custom loops); two-layer (universal WHAT-to-measure + per-layout WHERE-it-lives discovery).

- **`skills/multi-agent-audit/SKILL.md`** (326 lines) — orchestrator: read-only principle, two-layer framework-neutral design, Steps 0/0.5/1/3/4 workflow, inputs-to-confirm checklist, output-location convention (collab-repo `audit/` if exists, else `~/Workspace/audit-reports/`), invocation paths for Claude Code (subagent + direct) and code-puppy (read SKILL.md by path).
- **`agents/project-auditor.md`** — Claude Code subagent. Tool allow-list `Read, Grep, Glob, Bash, Write` (no `Edit`); `Write` only for the report file outside the audited repos. Refuse-to-fix policy explicit ("while you're in there, can you also..." → no).
- **`references/discovery.md`** — Step 0 procedure: declared roster sources (in priority order: `actors.yaml` → `manifest.yaml` → `agents/<name>/persona.yaml` → `AGENT.md` → CONVENTIONS.md), backlog source detection, coordination substrate, autonomy triggers, declared guardrails; layout-family heuristics (bootstrap v1.x / v0.x / vault-project / CrewAI / LangGraph / AutoGen / Copilot / custom); default 90-day window.
- **`references/actor-resolution.md`** — Step 0.5 inventory: enumerate from ALL sources (git committers + PR authors + PR REVIEWERS + mergers + CI bots/Apps + declared roster + coordination substrate); classify `human | autonomous | hybrid`; resolve N identities → 1 canonical actor (persona-prefix wins over email); non-committing-agents special case.
- **`references/drift-analysis.md`** — DUAL-LENS rule (INTENDED | ACTUAL | GAP + confidence) across 7 dimensions (agents / autonomy / reviewers / guardrails / routing / backlog / rituals); the load-bearing **enforced-vs-instructed** distinction; **operational fidelity** formula 0.00–1.00 with four interpretation bands; three drift archetypes (declared-not-operationalized, observed-undeclared, instructed-only-vs-enforced).
- **`references/metric-taxonomy.md`** — 7-category universal metric definitions (Throughput / PR review / Autonomy split + INTERVENTION TAX / Coordination + Network / DORA + flow / Quality + rework / Guardrail + ritual efficacy); per-axis 1–5 scoring rubric; **score-rollup-without-collapse** rule (do NOT compress 7 axes into a single number; name the failure-mode pattern instead).
- **`references/platform-integrations.md`** — read-only gh/git queries for every metric; explicit `gh api` GET-only enumeration; HTTPS-clone rule; pagination/sampling guidance; explicit don'ts (no `-X POST/PUT/PATCH/DELETE`, no `git commit/push/tag/rebase/merge/reset`).
- **`references/advanced-metrics.md`** — DORA four + extensions (merge-gate wait, WIP); network analysis with betweenness centrality + single-point-of-failure heuristic (top centrality > 2.5× mean); review/handoff/merge edge taxonomy.
- **`references/confidence-and-trends.md`** — confidence labels (`measured | inferred | not measurable`); full snapshot JSON v1.0 schema with worked example; trend-mode delta computation; window normalization rules (rate vs count metrics).
- **`references/bootstrap-adapter.md`** — agent-project-bootstrap v1.x layout adapter: exact mining commands for `manifest.yaml`, `agents/<slug>/persona.yaml`, `_handoff/`, `decisions/`, `findings/`, `wiki/`; commit-prefix attribution; enforced-vs-instructed cross-reference table; non-committing-agent reminder (Iris librarian, gh-actions PR review bots).
- **`references/report-template.md`** — markdown audit-report skeleton with 12 sections; placeholders only — every audit fills the same shape.
- **`assets/actors.example.yaml`** — declared-roster template; supports human/hybrid/autonomous classes, identity-resolution rules, declared guardrails, declared rituals, and an explicit `committing: false` marker for non-committing agents.
- **`assets/report-template.html`** — self-contained flat HTML + Chart.js dashboard template (stone/emerald palette matching TrellisIQ brand): verdict card, drift table, headline cards (intervention tax / autonomy donut / DORA / fidelity), per-persona bars, throughput trend, score radar, agent inventory table, ranked-opportunities list, trend section (renders only when ≥2 snapshots exist), methodology + caveats.
- **`scripts/collect_git_metrics.sh`** — read-only bash script that produces machine-readable JSON: commits-by-canonical-actor (persona-prefix honored), reverts/hotfixes/fixups, lines-by-author, cadence (active days), large-commit proxy (≥20 files = `git add -A` heuristic). Refuses to run inside the audited repo (working-directory guard); uses `git -C <repo>` exclusively.

**Status:** scoping → built. v1.2.0 will ship this skill alongside `agent-project-bootstrap`. First intended audit target: **GardenTwin** (real product with longest multi-agent history, especially timely given the 2026-06-10 workforce reduction — a before/after audit will quantify the intervention-tax impact). Distribution: personal use for now.

### Added — v1.0 close-out: §10.2 self-hosting outcome notes + §10.2/§4.6 docs

- **`references/v1-self-hosting-notes.md` (new)** — the comprehensive §10.2 "empirical backbone"
  writeup: which capability verbs surfaced from observed need, where the spec held, where it bent
  (`write_path` collapse, `pull_both_repos`→`sync_repos`, F7/F8), and what was discarded as YAGNI.
  Companion to the short `docs/LEARNINGS.md` index.
- **ADR-001 §4.6** — added a caption clarifying the "Resulting repo shape" diagram is the
  *emitted project's* structure (root `canon/` + `adapters/`), not the skill repo's. Resolves the
  long-standing adapter-location ambiguity.
- **`USING-WITH-CODE-PUPPY.md`** — added a "Vault commit / `/vc` on code-puppy" section (the two
  equivalents: the emitted `/vc-<slug>` command, or describing the workflow in plain language).
  *Reconciled from PR #15, which is now closed.*
- **`STATUS.md`** — v1.0 close-out marked complete (§10.2 + adapter-location done; Step 2 → `[x]`).

## [1.1.1] — 2026-06-08

Documentation-only release. Pulls the user-facing docs (README, `SKILL.md`) forward to the
runtime-agnostic v1.0/v1.1 architecture, adds the required "install canon + adapters" step to
`ORCHESTRATE.md`, and relabels the forward backlog `v1.1+` → `v1.2+` now that v1.1 has shipped.
No behavior or template-logic change.

### Changed — relabel the forward backlog `v1.1+` → `v1.2+` (v1.1 shipped)

- v1.1 is shipped, so the deferred-items backlog is now "v1.2+ candidates" (was the stale
  "v1.1+ candidates"). Updated `STATUS.md` (section heading + 2 internal refs), `CLAUDE.md`
  (versioning note), and `references/persona.schema.md` (the archetype-support pointer). Status
  sync only.

### Changed — reconcile user-facing docs to v1.0/v1.1 (documentation only)

A new-user doc review found the older user-facing layer (README, `SKILL.md`) had not been pulled
forward to the runtime-agnostic architecture. No behavior change — docs/templates only.

- **README** — the *Runtime support* table now shows **Claude Tier 3** (v1.1 enforced subagents),
  not just code-puppy; added a "Two generations — which path to use" section distinguishing the
  runtime-agnostic path (`START`/`ORCHESTRATE`/`PARTICIPATE` + `persona.yaml` + adapters) from the
  legacy v0.3.x emit modes; clarified `/plugin install` (URL or local clone).
- **`SKILL.md`** — bumped frontmatter `0.3.2 → 1.1.0`; **fixed the canonicality banner** (it
  claimed "vault is canonical, repo is a snapshot" — sunset since v1.0; now repo-canonical, matching
  `CLAUDE.md`); added a "Two paths" section so an invoked skill knows the runtime-agnostic
  entrypoints exist; corrected the stale "cron targeted for v0.4.0" note (shipped v0.3.2); updated
  the File manifest to list the v1 canon/adapters/entrypoints.
- **`ORCHESTRATE.md`** — added the required **"Install the canon + adapters into the project"**
  step; the entrypoints/adapters reference `canon/…` and `adapters/<runtime>/…` paths that no emit
  step previously created, which would have left future joiners pointing at missing files.
- **`persona.schema.md`** — added an **Archetype support** note (only `dev` is rendered
  end-to-end by v1 adapters; `autonomous-*`/`librarian` remain legacy `AGENT.md` templates) and
  surfaced the optional `runtime.adapters` override in the example.
- **`STATUS.md`** — added v1.1+ candidates: archetype parity in `persona.yaml`, native code-puppy
  skill packaging; noted `join-collab-project` shares vault-project's re-integration gap.
- **`.claude-plugin/plugin.json`** — modernized the plugin `description` from the v0.3.x
  "Claude Code project / three modes" framing to the runtime-agnostic v1 reality (multi-runtime,
  `persona.yaml` + adapters; legacy modes still listed).

## [1.1.0] — 2026-06-04

The Claude Tier-3 milestone. The Claude adapter now renders native subagents with an enforced
tool allow-list, plus the v1.0 close-out work. First properly cut release since v0.3.2
(plugin.json bumped 0.3.2 → 1.1.0; forward-only — the partial v1.0.0/v1.0.1 tags are left as-is).

### Added — `USING-WITH-CODE-PUPPY.md` quickstart

- New top-level guide for running the bootstrap on code-puppy, which does not auto-discover the
  Claude skill format. Documents the invoke-by-file-path flow (START → ORCHESTRATE → code-puppy
  adapter), the launch-from-project-root requirement, a verified file map, and the Tier-3
  enforcement note. README links to it from the Installation section.

### Added — Claude Tier-3 subagent rendering (ADR-001 §10.8; v1.1 feature)

- **`adapters/claude/HYDRATE.md` now renders BOTH tiers from one configurable adapter** (not
  two folders):
  - **Tier 3 (new)** — hydrates a persona into a native Claude **subagent** at
    `.claude/agents/<slug>.md` with an **enforced** `tools:` allow-list. Whole-tool denials
    become real (a read-only persona gets `Read, Grep, Glob` only; `Write`/`Edit`/`Bash` are
    absent and unavailable). Sub-tool denials (e.g. allow `open_pr`, deny `merge_pr`) stay
    instruction-only in the body — same honesty boundary the code-puppy adapter documents.
  - **Tier 2** — unchanged `CLAUDE.md` rendering (capabilities instructed).
  - Capability → Claude tool mapping for the enforced layer: `read_*`→`Read,Grep,Glob`;
    `write_code`/`write_path`→`Write,Edit`; `open_pr`/`run_tests`→`Bash`.
- **Tier selection via a runtime-neutral `adapters.<runtime>` config envelope** (keeps the
  canonical schemas free of runtime tool names):
  - `manifest.adapters.claude.tier` — project default (`auto` | `2` | `3`, default `auto`).
  - `persona.yaml > runtime.adapters.claude.tier` — per-persona override.
  - `auto` self-assesses subagent support and degrades to Tier 2 when the session can't host
    subagents (CI / constrained sub-sessions). Explicit `2`/`3` always wins.
- **Schemas** (`manifest.schema.md`, `persona.schema.md`) gain the optional `adapters.<runtime>`
  / `runtime.adapters.<runtime>` override envelope (v1.1; additive, forward-compatible).
- **`tests/bi_runtime_accept.py`** extended: the same harness now asserts code-puppy (Tier 3) ≡
  Claude Tier 2 ≡ Claude Tier 3 produce an identical behavior contract — not a second
  top-level test. Both fixtures (dev `tess`, read-only `rex`) pass.
- **ADR-001** §10.5 / §10.8 updated (Tier-3 shipped; config-location rationale recorded).

### Fixed — correct the bi-runtime test invocation in docs

- The documented command `python tests/bi_runtime_accept.py` fails with `ModuleNotFoundError:
  yaml` on a stock interpreter. Corrected `CLAUDE.md` (release workflow + Testing section) and
  `CONTRIBUTING.md` to `uv run --with pyyaml python tests/bi_runtime_accept.py`, matching the
  harness's own dependency need.
- Fixed the harness docstring, which still pointed at the pre-move path
  `wip/acceptance/bi_runtime_accept.py`, to the current `tests/bi_runtime_accept.py`.

### Added — `docs/LEARNINGS.md` (minimum-viable lessons index)

- **`docs/LEARNINGS.md` (new)** captures the ADR-001 §10 dogfood lessons (`L1`–`L3`) and proven
  rules (`Proven #1`–`#2`). Resolves four previously dangling references — in
  `references/capability-vocab.v1.md` (proven #2, L3), `adapters/claude/HYDRATE.md` (L3), and
  `adapters/generic/HYDRATE.md` (L3). Minimum-viable by design; the comprehensive §10.2
  self-hosting outcome notes remain a tracked v1.0 close-out item in `STATUS.md`.

### Changed — de-Claude the emitted `COORDINATION.md` (ADR §10.6, finishes Step 6)

- Removed the three runtime-isms from the emitted `COORDINATION.md` template, mirroring PR #7's
  treatment of `CONVENTIONS.md`:
  - **Session-start checklist** — replaced the `git pull` / `grep` / `gh issue list` bash blocks
    with intent-level steps that point at `adapters/<runtime>/HYDRATE.md` for concrete syntax and
    `references/capability-vocab.v1.md` for the verbs.
  - **Ticket lifecycle** — abstracted the `gh issue edit … --add-assignee/--add-label`
    self-assignment to backlog-source language (`gh` is one runtime's shell, not the canon).
  - **Async handoff protocol** — generalized the Iris-specific "personal librarian" paragraph to
    any librarian-equivalent persona (`for: librarian`), and dropped the Obsidian-specific "vault"
    wording. Runtime-neutral, matching the canon. Cosmetic for existing scaffolds (no behavior
    change).

### Changed — meta-docs refresh for v1.0 development surface

- **`CLAUDE.md` rewritten** to reflect the post-ADR-001 reality: this repo is the canonical home and active development surface for v1.0+; the v0.x "vault canonical, repo snapshot" rule is sunset. Updates repo layout, persona expectation for a fresh agent landing in the repo, and release workflow.
- **`STATUS.md` (new)** at repo root tracks ADR-001 §10 progress (most of v1.0 shipped; `COORDINATION.md` de-Claude + §10.2 self-hosting outcome notes still open) and v1.1 candidates (Claude Tier-3 subagents, vault-project re-integration, cron live-wiring, additional adapters). Update on every PR that ships a step.
- **ADR-001 body header** corrected: `Status: Proposed` → `Status: Accepted (2026-05-30)`. Frontmatter already said accepted; this fixes the internal inconsistency.
- **`CONTRIBUTING.md`** adds a **"Documentation is part of every PR"** section codifying the rule that affected ADRs, `CLAUDE.md`, `README.md`, `CHANGELOG.md`, and `STATUS.md` updates land in the same PR as the code change — never as a follow-up. Surfaces explicit checklist + cosmetic-changes exception. Also notes the `uv run --with pyyaml python tests/bi_runtime_accept.py` gate for adapter / spec / canonical-contract changes.

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
