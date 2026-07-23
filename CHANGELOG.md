# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added — baron CLI M1–M3 (Phase 2: conventions → mechanisms, ADR-003)

- **`docs/adr/ADR-003-baron-cli.md`** (accepted 2026-07-22) — the `baron` CLI decisions:
  markdown/git substrate as the only database; typer+pyyaml-only dependency policy (git/gh
  via subprocess); forge Protocol with GitLab-as-plugin backlog (`baron.forges` entry-point
  group); ledger ID allocation via push-retry; archive-not-delete handoff lifecycle.
  Motivations traced to field evidence: three F-number collisions, the 2026-07-22
  triple-stranding incident, markdown LOCK-commit races, 18/40 open handoffs
  (badminton-analyzer), and enforcement theater (GardenTwin audit, operational fidelity 0.53).
- **`cli/`** — the `baron-cli` package (src layout, Python ≥ 3.10, console script `baron`):
  - **M1 `baron validate [PATH]`** — persona.yaml/manifest.yaml validation against
    declarative schemas (`cli/src/baron/schemas.py`) formalized from the prose specs;
    embeds the FROZEN 10-verb capability vocabulary with a drift-guard test that re-parses
    `references/capability-vocab.v1.md`. Checks parse/fields/types/verbs/allow-deny
    overlap/unfilled placeholders; template dirs (`assets/collab-repo/`, `legacy/`) skipped
    on discovery. `--json`; exit 0 clean / 1 errors.
  - **M2 `baron status [--fetch] [--sla N] [--json]`** — divergence & staleness report:
    ahead/behind origin default branch, dirt, unmerged local branches with age, open
    handoffs past SLA, ledger staleness vs code-repo activity (labeled heuristic), stale
    `wiki/status.md`. Acceptance test builds a synthetic topology reproducing the three
    2026-07-22 stranding classes. Exit 0 green / 1 any red.
  - **M3 ledgers & handoffs** — `baron finding new` / `baron decision new` (max-ID parse of
    both heading and table-row forms, push-retry renumbering on rejection, injectable
    clock, `--no-push`); `baron handoff create/close/list` (standard frontmatter; close =
    status flip + `closed:` date + optional note + `git mv` to `_handoff/archive/YYYY/`);
    `baron index` (marker-delimited summary block in `_handoff/README.md` + report-only
    numbering verification). Race acceptance test: two clones allocate the same F-number;
    the rejected writer renumbers and both land.
- **`references/manifest.schema.md` v1.2** — optional `workspace.clones` /
  `workspace.worktrees_root` fields (local persona working copies for `baron status`
  sweeps); commented example block in `manifest.example.yaml`.
- **`docs/BACKLOG.md`** — GitLab forge plugin design sketch (entry-point discovery, same
  Protocol, `forge: gitlab` manifest key) plus consciously deferred M1–M3 items; worktree
  topology tracked as baron M6.
- **CI** — new `baron-cli` job (`uv run --project cli pytest cli/tests`); the stdlib-only
  jobs are untouched.

## [1.4.0] — 2026-07-22

The credibility-debt release: one front door, honest artifacts, real tests, and the
field-proven July-2026 ways-of-working (ADR-002).

### Changed — one front door (legacy path quarantined)

- **`SKILL.md` rewritten as a thin front door** (frontmatter bumped `1.1.0 → 1.4.0`, gains a
  `description:` for skill discovery). All new-project creation and joining routes through
  `assets/collab-repo/START.md` → `ORCHESTRATE.md` / `PARTICIPATE.md`; the legacy modes are a
  one-line pointer.
- **Legacy v0.3 path moved to `legacy/`** at the repo root: `legacy/vault/`,
  `legacy/workspaces/` (the template trees only the legacy modes consume) and
  `legacy/SKILL-v0.3.md` (the three-mode emit instructions, verbatim). `legacy/README.md`
  marks it deprecated/unmaintained, kept for existing v0.x projects.
- **`.claude-plugin/plugin.json`** `1.3.0 → 1.4.0`; description reflects the one-front-door +
  legacy-quarantine reality. Version sync with `SKILL.md` is now lint-enforced.
- **Doc dedup:** the v0→v1 migration story now lives ONLY in ADR-001 + this changelog;
  `README.md`, `SKILL.md`, `CLAUDE.md`, `STATUS.md`, and `docs/LEARNINGS.md` trimmed to
  one-line pointers. `CLAUDE.md`/`STATUS.md` no longer claim "v1.0 shipped / v1.1 candidates"
  as the current state.

### Added — missing/broken artifacts fixed

- **`assets/collab-repo/manifest.example.yaml`** — realistic worked example of the
  `manifest.schema.md` contract (two interactive dev personas + librarian, two-repo pattern).
- **`agents/__DEV__/persona.yaml` is a real template** — was a verbatim copy of the
  `tests/examples/tess` fixture (hardcoded `persona: Tess`); now uses the same
  `{{PLACEHOLDER}}` tokens as its sibling `AGENT.md`.
- **Archetype parity (closes an ADR-001 §10.8 deferred item):** `persona.yaml` templates for
  `librarian`, `__AUTONOMOUS_EVENT__`, and `__AUTONOMOUS_CRON__` alongside their `AGENT.md`s,
  capability sets drawn from the frozen v1 vocabulary. `persona.schema.md`'s "these archetypes
  only exist as legacy AGENT.md templates" caveat replaced with the supported-archetype table.
- **`docs/notes/CORRECTION-wibey-vs-codepuppy.md`** and **`docs/notes/code-puppy-capability-map.md`**
  — reconstructed stubs (originals were cited by `capability-vocab.v1.md` and the code-puppy
  adapter since v1.0 but never committed; marked as reconstructed).

### Added — July-2026 ways-of-working (ADR-002; field-proven on badminton-analyzer)

- **`docs/adr/ADR-002-ways-of-working-2026-07.md`** (accepted 2026-07-22) — decisions + evidence.
- **Emitted `CONVENTIONS.md`:** single-GitHub-account constraint as a stated first principle
  (every gate enforced by persona capability, never GitHub perms); "everything material gets
  a handoff" (findings, decisions, corrections; numbers are proposed to the Librarian, never
  self-assigned); machine-local persona-state convention (`~/.claude/agent-state/` analog +
  snapshot-restore).
- **Emitted `COORDINATION.md`:** Lock pattern is now lock-via-open-PR + `lock:*` labels + a CI
  guard (CODEOWNERS explicitly rejected — no enforcement without branch protection); Owner
  pattern is an evidence gate; new "Review and merge" section (SHA-bound Reviewer verdicts,
  Merger preconditions); persona.yaml CI validation documented.
- **Reviewer + Merger persona archetype templates** (`agents/__REVIEWER__/`,
  `agents/__MERGER__/`, each `persona.yaml` + `AGENT.md`): adversarial fresh-context reviewer
  publishing SHA-bound verdict comments; merger holding the project's only `merge_pr` as a
  precondition gate.
- **Librarian template corrections** (ADR-002 §6): `open_pr` allowed; event-triggered
  reconcile preferred with cron as backstop.

### Changed — real tests + CI

- **Adapters carry a normalized machine-readable capability map** (`capability-map:v1` marker
  in each `adapters/*/HYDRATE.md`): one row per frozen v1 verb — class, runtime-neutral
  grants category, runtime tools, deny-enforcement claim. The claude/code-puppy maps also gain
  rows for `merge_pr`/`push_main`/`force_push`/`edit_other_personas` (needed now that merger
  and librarian archetypes can ALLOW them).
- **`tests/bi_runtime_accept.py` rewritten** — it previously re-implemented the
  capability→tool mapping in Python and tested itself (tautological). It now PARSES the
  actual HYDRATE.md tables + `capability-vocab.v1.md` and asserts: every v1 verb mapped in
  every adapter; tess/rex fixtures hydrate to an equivalent contract across adapters
  (identity, grants, denies, whole-tool denial honoring); enforcement-tier claims consistent
  (generic all-instructed; Tier-3 adapters enforced exactly for whole-tool verbs). Now
  stdlib-only (no PyYAML).
- **`tests/lint_repo.py` (new, stdlib):** unfilled `{{placeholder}}` tokens outside template
  dirs; dead relative markdown links repo-wide; fixture-name leaks ("Tess"/"Rex") in shipped
  templates; plugin.json ↔ SKILL.md version sync.
- **`.github/workflows/ci.yml` (new):** runs both tests with plain python on push + PR.
- **code-puppy adapter worked example** re-anchored to the `tests/examples/tess` fixture and
  de-named (fixture display names no longer appear in shipped templates); its stale v0 verb
  list (`write_findings`/`write_handoff`) corrected to the v1 `write_path` form.
- **`CLAUDE.md` / `CONTRIBUTING.md`** test instructions updated (`uv run --with pyyaml` no
  longer needed).

## [1.3.0] — 2026-06-12

The first-real-audit-feedback release. v1.2.0 shipped the `multi-agent-audit` skill and Iris ran it against GardenTwin within hours; the audit's own write-up identified 13 substantive failures + a missing timeline feature. v1.3 closes all 13 and adds the timeline. Self-validating loop completed in <24h.

### Added — `multi-agent-audit` skill v1.3 (closes all 13 v1.2.0 findings + timeline feature)

#### Multi-substrate Agents lens (Finding #1)

The biggest v1.2 framing flaw was overweighting the `git log` lens for the Agents drift dimension. v1.3 codifies the multi-substrate rule in `references/drift-analysis.md` and `references/bootstrap-adapter.md`:

- **Agents identity** is mined from **five substrates** (GitHub `agent-*` labels, vault `_handoff/` `from:`/`for:` fields, dev-log/EOD/session-log frontmatter, optional persona-prefix commits, and `git log` as a last-resort fallback). Git-log identity collision is the *rule* for single-human multi-agent projects, NOT pathological drift.
- `bootstrap-adapter.md` now ships a per-substrate presence vector + operationally-present threshold.

#### Conv-commits filter (Finding #8)

`scripts/collect_git_metrics.sh` now defaults `CONV_COMMITS_FILTER=1` — Conventional Commits keywords (`feat`/`fix`/`docs`/`chore`/`refactor`/`test`/`ci`/`style`/`perf`/`build`/`revert`) bucket into a new `commits_by_conv_commit_type` field rather than polluting `commits_by_persona_prefix`. New `PERSONA_PREFIXES` env supports an explicit allowlist; everything else goes to `commits_by_other_prefix`. Smoke-tested.

#### Snapshot schema v1.0 → v1.1 — `addenda:` + `auditor_independence:` (Findings #3, #6)

`references/confidence-and-trends.md` defines schema v1.1 (additive — old snapshots still readable):

- **`addenda:` array** on the snapshot is the ONE allowed edit to a shipped point-in-time record. `addenda[*].revised_values` overrides any body field via dot-path; `trend_reader.py` applies them automatically before computing deltas.
- **`audit_run.auditor_independence`** flag captures whether the auditor is itself a participant in the audited project. Renderer surfaces this as a callout banner. Required starting v1.3; surfaces conflict-of-interest in §11 Methodology.

#### Weighted operational-fidelity formula (Finding #12)

`references/metric-taxonomy.md` adds the optional weighted formula. Default per-dimension weights: Guardrails 2.0, Reviewers 1.5, Agents/Autonomy/Routing/Backlog 1.0 each, Rituals 0.5. Equal-weight remains the default; weighted is opt-in.

#### Timeline feature (new — user request)

A new §9.5 Timeline section in the markdown report + horizontal SVG block in the HTML dashboard, surfacing the **important events** in the audit window (releases, ADR creations, roster changes, CONVENTIONS/COORDINATION changes, incidents, audit snapshots, large features).

- **`references/timeline.md`** (new) — event taxonomy, detection rules per type, importance heuristic 1–10, output formats.
- **`scripts/extract_timeline.py`** — detector for 8 event types from a code repo + optional coordination/vault path. Importance scoring with adjacency-aware label staggering. Emits markdown or JSON.
- HTML SVG in `assets/report-template.html`: markers colored by type and sized by importance; week-tick axis; legend; labels for importance ≥7.

#### Five Python helpers — stdlib-only (Findings #4 #5 #9 #10 #11)

- **`scripts/trend_reader.py`** — walks `snapshots/`, applies `addenda[*].revised_values`, computes deltas on the canonical trend metrics, emits §10 Trend markdown OR JSON. Handles single-snapshot, schema mismatch, window-size mismatch gracefully.
- **`scripts/compute_centrality.py`** — Brandes' betweenness centrality on the coordination network (handoffs + optional reviews/merges). SPOF flag at 2.5× mean ratio. **Smoke-test against the vault's handoff graph produced Iris ratio 4.7× — sharper than the v1.2.0 hand-waved 2.1× estimate**, demonstrating the script generates findings the human-driven audit missed.
- **`scripts/parse_coverage.py`** — auto-detects Istanbul / LCOV / Cobertura formats; optional `--baseline` for delta computation; normalized output schema.
- **`scripts/persona_attribution.py`** — joins `agent-*` claim labels → PRs closing those issues → files touched per persona. The v1.3 fix for the v1.2.0 identity-collision finding using the multi-substrate lens.
- **`scripts/extract_timeline.py`** — see Timeline feature above.

#### HTML dashboard renderer (Finding #2 — "HTML dashboard wasn't produced")

- **`scripts/render_report.py`** (new, ~350 lines, stdlib) — fills the template's 18 simple `{{X}}` placeholders + 10 `<!-- INSERT:X -->` block markers; auto-detects template location relative to the script; injects a single JSON `data` object for the Chart.js script block (no inline mustache).
- **`assets/report-template.html` rewritten** — mustache-style loops replaced with INSERT markers (renderer-fillable, no template engine dep). Adds: per-persona scorecards grid, timeline SVG section, auditor-independence callout, false-win callout, addenda card.

#### Short-form executive-summary mode (Finding #13)

- **`references/short-form-mode.md`** — spec + markdown/HTML templates.
- **`scripts/render_short.py`** — stdlib renderer. Markdown: ~1 KB. HTML: ~4 KB (no Chart.js dependency). Applies addenda like the full renderer.

#### Subagent isolation smoke test (Finding #10 — "subagent-isolation test didn't happen")

- **`tests/subagent_isolation_smoke.md`** — runbook for verifying the `project-auditor` subagent's read-only contract. Static checks + manual runtime tests (Edit-injection refusal, destructive-shell refusal, audited-repo-unchanged verification). Honest about tool-enforced vs instruction-enforced layers.
- **`tests/verify_readonly_contract.sh`** — automated static portion: 6 checks (subagent file exists, tools list correct, Edit absent, no destructive `gh api -X` in scripts, no destructive `git`/`gh` in `.sh` code or `.py` subprocess calls, SKILL.md retains read-only language). All 6 pass on the v1.3 skill.

#### Coverage-parser documentation (Batch 2 companion)

- **`references/coverage-parsers.md`** — documents `parse_coverage.py` usage, supported formats, project-type-specific discovery rules, baseline-vs-current workflow, recommended remediation when reports are absent.

### Changed — meta-docs for v1.3

- **`SKILL.md`** — inputs-to-confirm checklist gains independence flag, weighting choice, timeline-yes/no. File inventory updated for the v1.3 layout (scripts/, tests/).
- **`STATUS.md`** — v1.3 marked shipped; v1.4+ candidates updated.
- **`README.md`** — sister-skill section mentions v1.3 enhancements.
- **`.claude-plugin/plugin.json`** — version 1.2.0 → 1.3.0; description mentions short-form mode + timeline feature.
- **`skills/multi-agent-audit/.gitignore` (new)** — prevents accidental `__pycache__/` tracking.

### Validation

The v1.3 skill running on its own coordination substrate (vault handoffs) already produced findings sharper than the v1.2 human-driven audit. Re-audit of GardenTwin with v1.3 is the formal validation step; first opportunity for trend-mode-with-overrides to fire on a real project.

## [1.2.0] — 2026-06-12

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
