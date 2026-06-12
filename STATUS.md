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

## v1.2 — in progress (next release)

- [x] **`multi-agent-audit` skill + `project-auditor` subagent.** New sister skill at `skills/multi-agent-audit/` for grading multi-agent projects. Read-only by construction; headline metric is INTERVENTION TAX (human touches per autonomous task). Framework-neutral (agent-project-bootstrap, CrewAI, LangGraph, AutoGen, Copilot agents, custom loops); two-layer (universal metrics + per-layout adapters). Built 2026-06-12 on branch `feat/multi-agent-audit-skill`: 14 files / 3122 lines including SKILL.md, 9 references (discovery, actor-resolution, drift-analysis, metric-taxonomy, platform-integrations, advanced-metrics, confidence-and-trends, bootstrap-adapter, report-template), assets (actors.example.yaml + Chart.js HTML dashboard), `collect_git_metrics.sh` (read-only bash → JSON), and the Claude Code subagent. **Distribution:** personal use for now. **First intended audit target:** GardenTwin (timely given the 2026-06-10 workforce reduction — before/after audit will quantify the intervention-tax impact). See PR #TBD.

## v1.1 — shipped

- [x] **Claude Tier-3 subagent rendering.** `adapters/claude/HYDRATE.md` now renders BOTH tiers from one configurable adapter: Tier 2 (`CLAUDE.md`, instructed) and Tier 3 (native subagent at `.claude/agents/<slug>.md` with an enforced `tools:` allow-list — whole-tool denials are real; sub-tool denials stay instructed, matching the code-puppy contract). Tier resolved from a **runtime-neutral** `adapters.claude.tier` config (`auto` | `2` | `3`, default `auto`; project default in `manifest.adapters.claude.tier`, per-persona override in `persona.yaml > runtime.adapters.claude.tier`). `auto` self-assesses subagent support and degrades to Tier 2 gracefully. `tests/bi_runtime_accept.py` asserts code-puppy ≡ Claude-Tier-2 ≡ Claude-Tier-3 for both fixtures. Config-location decision (namespaced envelope vs. bare `claude_tier`) recorded in ADR-001 §10.8 amendment.

## v1.2+ candidates (per ADR §10.8 deferred list)

> v1.1 is shipped (Claude Tier-3, above). These are post-v1.1 / next-minor candidates.

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
