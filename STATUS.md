# STATUS — agent-project-bootstrap

Tracks v1.0 close-out items and v1.1 progress against ADR-001 §10. Update on every PR that ships a step (per `CONTRIBUTING.md`).

**ADR:** [`docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md`](docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md)

## v1.0 — shipped 2026-06-03

The runtime-agnostic milestone is **RELEASED** (v1.0.0 + v1.0.1).

### §10 execution plan — final status

- [x] **Step 1** — Write `adapters/code-puppy/HYDRATE.md` end-to-end for one persona. *Shipped in PRs #2 / #4.*
- [x] **Step 2** — Ship work project on code-puppy; validate adapter against real use. *Self-hosting validated — code-puppy built the v1.0 implementation on this very repo (PRs #2, #4, #7, #8); the `tests/bi_runtime_accept.py` harness exercises the contract automatically. The "outcome notes" writeup is now authored at `references/v1-self-hosting-notes.md` (§10.2 below).*
- [x] **Step 3** — Derive the canonical contract from observed needs. *Shipped.* References at `skills/agent-project-bootstrap/references/{capability-vocab.v1, persona.schema, manifest.schema}.md`; neutral entrypoints at `skills/agent-project-bootstrap/assets/collab-repo/{START, ORCHESTRATE, PARTICIPATE}.md`.
- [x] **Step 4** — Write `adapters/generic/HYDRATE.md` (Tier-1 fallback). *Shipped.*
- [x] **Step 5** — Write `adapters/claude/HYDRATE.md` (Tier 2 — CLAUDE.md rendering). *Shipped.* Tier-3 (Claude native subagents, enforced `tools:` allow-list) **shipped in v1.1** as one configurable adapter — see "v1.1 — shipped" below.
- [x] **Step 6** — De-Claude the neutral docs.
  - [x] `skills/agent-project-bootstrap/assets/collab-repo/CONVENTIONS.md` (PR #7)
  - [x] `skills/agent-project-bootstrap/assets/collab-repo/COORDINATION.md` (PR #12)
- [x] **Step 7** — Cut v1.0 release. *Shipped 2026-06-03 (v1.0.0 + v1.0.1).*
- [ ] **Step 8** — Deferred items (post-1.0). See "v1.2+ candidates" below.

## v1.0 close-out items — ✅ all complete

These finished v1.0 (none blocked the release); all three are now done:

- ~~**§10.6 — de-Claude `COORDINATION.md`.**~~ **Done (PR #12).** Session-start checklist now states intent (capabilities, not shell commands) and points at `adapters/<runtime>/HYDRATE.md`; the `gh issue edit` self-assignment was abstracted to backlog-source language; the Iris-specific personal-librarian paragraph was generalized to any librarian-equivalent persona. Matches the canon's tone and the PR #7 treatment of `CONVENTIONS.md`.
- ~~**§10.2 — outcome notes from the self-hosting validation.**~~ **Done.** The comprehensive writeup is now at `references/v1-self-hosting-notes.md` — which capability verbs surfaced from observed need, where the spec held, where it bent (e.g. the `write_path` collapse, `pull_both_repos`→`sync_repos`, F7/F8), and what was discarded as YAGNI. `docs/LEARNINGS.md` remains the short index; this is the empirical-backbone companion.
- ~~**Adapter location interpretation.**~~ **Resolved.** ADR §4.6 now carries a caption making explicit that the "Resulting repo shape" diagram is the EMITTED PROJECT's structure (root `canon/` + `adapters/`), not the skill repo's (`skills/agent-project-bootstrap/assets/collab-repo/` + `references/`). No code move; consistent with `ORCHESTRATE.md` step 2a.

## v1.3 — shipped 2026-06-12

The first-real-audit-feedback release. v1.2.0 shipped the `multi-agent-audit` skill; Iris ran it against GardenTwin within hours; the audit's own write-up identified 13 substantive failures + a missing timeline feature. v1.3 closes all 13 and adds the timeline. Self-validating loop completed in <24h.

- [x] **Multi-substrate Agents lens** — codified in `drift-analysis.md` + `bootstrap-adapter.md`. Git-log identity collision is the rule, not the exception. Substrates: claim labels + handoffs + frontmatter + prefix-commits + git-author.
- [x] **Conv-commits filter** in `collect_git_metrics.sh` (CONV_COMMITS_FILTER env, PERSONA_PREFIXES allowlist). Smoke-tested.
- [x] **Snapshot schema v1.1** — additive `addenda:` array + `auditor_independence` object. The one allowed edit to shipped snapshots; trend-mode reader applies overrides before deltas.
- [x] **Weighted operational-fidelity formula** (opt-in). Default weights privilege Guardrails 2.0, Reviewers 1.5.
- [x] **Timeline feature** — new §9.5 in reports + horizontal SVG in HTML dashboard. `extract_timeline.py` + `references/timeline.md` define event taxonomy, importance scoring, detection rules.
- [x] **5 stdlib Python helpers**: `trend_reader.py`, `extract_timeline.py`, `compute_centrality.py` (Brandes' betweenness), `parse_coverage.py` (Istanbul/LCOV/Cobertura), `persona_attribution.py`.
- [x] **HTML dashboard renderer** — `render_report.py` fills `{{X}}` placeholders + `<!-- INSERT:X -->` markers; template rewritten without inline mustache. Per-persona scorecards + timeline + addenda + auditor-independence callout sections added.
- [x] **Short-form mode** — `render_short.py` produces 1 KB markdown / 4 KB HTML executive summary alongside the full report.
- [x] **Subagent isolation test** — `tests/subagent_isolation_smoke.md` runbook + `tests/verify_readonly_contract.sh` static checker (6 checks, all pass).
- [x] **Coverage-parser documentation** — `references/coverage-parsers.md` (companion to `parse_coverage.py`).

## v1.2 — shipped 2026-06-12

- [x] **`multi-agent-audit` skill + `project-auditor` subagent.** New sister skill at `skills/multi-agent-audit/` for grading multi-agent projects. Read-only by construction; headline metric is INTERVENTION TAX (human touches per autonomous task). Framework-neutral (agent-project-bootstrap, CrewAI, LangGraph, AutoGen, Copilot agents, custom loops); two-layer (universal metrics + per-layout adapters). Built 2026-06-12 on branch `feat/multi-agent-audit-skill`: 14 files / 3122 lines including SKILL.md, 9 references (discovery, actor-resolution, drift-analysis, metric-taxonomy, platform-integrations, advanced-metrics, confidence-and-trends, bootstrap-adapter, report-template), assets (actors.example.yaml + Chart.js HTML dashboard), `collect_git_metrics.sh` (read-only bash → JSON), and the Claude Code subagent. **Distribution:** personal use for now. **First intended audit target:** GardenTwin (timely given the 2026-06-10 workforce reduction — before/after audit will quantify the intervention-tax impact). See PR #TBD.

## v1.1 — shipped

- [x] **Claude Tier-3 subagent rendering.** `adapters/claude/HYDRATE.md` now renders BOTH tiers from one configurable adapter: Tier 2 (`CLAUDE.md`, instructed) and Tier 3 (native subagent at `.claude/agents/<slug>.md` with an enforced `tools:` allow-list — whole-tool denials are real; sub-tool denials stay instructed, matching the code-puppy contract). Tier resolved from a **runtime-neutral** `adapters.claude.tier` config (`auto` | `2` | `3`, default `auto`; project default in `manifest.adapters.claude.tier`, per-persona override in `persona.yaml > runtime.adapters.claude.tier`). `auto` self-assesses subagent support and degrades to Tier 2 gracefully. `tests/bi_runtime_accept.py` asserts code-puppy ≡ Claude-Tier-2 ≡ Claude-Tier-3 for both fixtures. Config-location decision (namespaced envelope vs. bare `claude_tier`) recorded in ADR-001 §10.8 amendment.

## v1.4+ candidates

> v1.3 closed all 13 self-review findings from v1.2's first real audit. The candidates below are either deferred items from earlier ADRs (§10.8) or new items surfaced by v1.3 work.

### multi-agent-audit skill candidates

- **Per-runtime adapter docs** for non-bootstrap layouts (CrewAI / LangGraph / AutoGen / Copilot agents) — currently the skill ships a heuristic discovery path for these; dedicated `references/<runtime>-adapter.md` files when first real audit demands.
- **Sub-tool scoping for `Bash`** in `project-auditor.md` once Claude Code supports `Bash(git log:*, gh api:*)` — would harden the read-only contract from instruction-enforced to tool-enforced for shell commands.
- **Weekly throughput histogram** in the snapshot schema — currently `metrics.throughput` aggregates over the whole window; charts that need per-week buckets (throughput trend in the dashboard) get empty data.
- **`coverage.py` binary `.coverage` parser** — currently we require `coverage xml` export; a direct binary parser would close that gap.
- **Native Go cover profile parser** — currently unsupported.
- **Trend-mode auto-trigger** from `render_report.py` (currently the auditor invokes `trend_reader.py` separately).
- **HTML email-friendly compact mode** — the short-form HTML is desktop-styled; an email-client-compatible variant would help digest distribution.

### agent-project-bootstrap candidates (per ADR §10.8 deferred list)

- **vault-project mode re-integration.** v1.0 left vault-project on v0.3.x rails. Bringing it under the runtime-agnostic architecture means either porting it to use the `persona.yaml` + adapter pattern, or formally deprecating it. (Same applies to `join-collab-project` mode.)
- **Archetype parity in `persona.yaml` + adapters.** The runtime-agnostic spec renders only the `dev` archetype end-to-end. `autonomous-event`, `autonomous-cron`, and `librarian` still live only as legacy `AGENT.md` templates — port them so those archetypes hydrate via `persona.yaml` on each runtime (see `references/persona.schema.md` "Archetype support").
- **Native code-puppy skill packaging.** code-puppy doesn't auto-discover the Claude `SKILL.md` format, so it's invoked by file path today (`USING-WITH-CODE-PUPPY.md`). A native code-puppy skill wrapper would remove the manual step.
- **Cron / failover live wiring.** v1.0 emits cron stubs and failover runbooks but doesn't wire schedulers automatically. Cross-runtime cron auto-registration is real engineering work.
- **Additional adapters** — Codex, Wibey, etc. Add when there's a forcing function (a real project on that runtime).

## How to use this file

- Update on every PR that ships a step.
- New deferred items get added under "v1.2+ candidates."
- Completed items move from `[~]` / `[ ]` to `[x]`.
- Per `CONTRIBUTING.md`, this file is part of every PR that ships a §10 step.
