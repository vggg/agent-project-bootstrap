# STATUS — agent-project-bootstrap

Tracks v1.0 close-out items and v1.1 progress against ADR-001 §10. Update on every PR that ships a step (per `CONTRIBUTING.md`).

**ADR:** [`docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md`](docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md)

## v1.0 — shipped 2026-06-03

The runtime-agnostic milestone is **RELEASED** (v1.0.0 + v1.0.1).

### §10 execution plan — final status

- [x] **Step 1** — Write `adapters/code-puppy/HYDRATE.md` end-to-end for one persona. *Shipped in PRs #2 / #4.*
- [~] **Step 2** — Ship work project on code-puppy; validate adapter against real use. *Self-hosting underway — code-puppy has been doing the v1.0 implementation on this very repo (PRs #2, #4, #7, #8). The `tests/bi_runtime_accept.py` harness exercises the contract automatically; the "outcome notes" writeup (what worked, what didn't, what vocabulary surfaced from observed need) hasn't been authored yet.*
- [x] **Step 3** — Derive the canonical contract from observed needs. *Shipped.* References at `skills/agent-project-bootstrap/references/{capability-vocab.v1, persona.schema, manifest.schema}.md`; neutral entrypoints at `skills/agent-project-bootstrap/assets/collab-repo/{START, ORCHESTRATE, PARTICIPATE}.md`.
- [x] **Step 4** — Write `adapters/generic/HYDRATE.md` (Tier-1 fallback). *Shipped.*
- [x] **Step 5** — Write `adapters/claude/HYDRATE.md` (Tier 2 — CLAUDE.md rendering). *Shipped.* Tier-3 (Claude native subagents, enforced `tools:` allow-list) **shipped in v1.1** as one configurable adapter — see "v1.1 — shipped" below.
- [x] **Step 6** — De-Claude the neutral docs.
  - [x] `skills/agent-project-bootstrap/assets/collab-repo/CONVENTIONS.md` (PR #7)
  - [x] `skills/agent-project-bootstrap/assets/collab-repo/COORDINATION.md` (PR #12)
- [x] **Step 7** — Cut v1.0 release. *Shipped 2026-06-03 (v1.0.0 + v1.0.1).*
- [ ] **Step 8** — Deferred items (post-1.0). See "v1.1+ candidates" below.

## v1.0 close-out items

These finish v1.0 but didn't block the release:

- ~~**§10.6 — de-Claude `COORDINATION.md`.**~~ **Done (PR #12).** Session-start checklist now states intent (capabilities, not shell commands) and points at `adapters/<runtime>/HYDRATE.md`; the `gh issue edit` self-assignment was abstracted to backlog-source language; the Iris-specific personal-librarian paragraph was generalized to any librarian-equivalent persona. Matches the canon's tone and the PR #7 treatment of `CONVENTIONS.md`.
- **§10.2 — outcome notes from the self-hosting validation.** *(partial)* `docs/LEARNINGS.md` now exists as a minimum-viable lessons index (L1–L3, Proven #1–#2) and resolves the references that cited it. **Still TBD:** the comprehensive outcome notes — which capability verbs surfaced from observed need (vs. designed up-front), where the spec held up well, where it bent, what was discarded as YAGNI. This is the empirical-backbone evidence the §10 plan promises; the minimal index is not a substitute for it.
- **Adapter location interpretation.** Implementation puts adapters at `skills/agent-project-bootstrap/assets/collab-repo/adapters/` (emit-time templates that copy to `<target-project>/adapters/` at scaffold time). ADR §4.6's "Resulting repo shape" diagram shows `adapters/` at repo root — which describes the EMITTED PROJECT's structure, not this repo's. The two are consistent, but the ADR diagram is ambiguous. Either amend the diagram caption to make this explicit OR add a clarifying paragraph in §4.6. No code move needed.

## v1.1 — shipped

- [x] **Claude Tier-3 subagent rendering.** `adapters/claude/HYDRATE.md` now renders BOTH tiers from one configurable adapter: Tier 2 (`CLAUDE.md`, instructed) and Tier 3 (native subagent at `.claude/agents/<slug>.md` with an enforced `tools:` allow-list — whole-tool denials are real; sub-tool denials stay instructed, matching the code-puppy contract). Tier resolved from a **runtime-neutral** `adapters.claude.tier` config (`auto` | `2` | `3`, default `auto`; project default in `manifest.adapters.claude.tier`, per-persona override in `persona.yaml > runtime.adapters.claude.tier`). `auto` self-assesses subagent support and degrades to Tier 2 gracefully. `tests/bi_runtime_accept.py` asserts code-puppy ≡ Claude-Tier-2 ≡ Claude-Tier-3 for both fixtures. Config-location decision (namespaced envelope vs. bare `claude_tier`) recorded in ADR-001 §10.8 amendment.

## v1.1+ candidates (per ADR §10.8 deferred list)

- **vault-project mode re-integration.** v1.0 left vault-project on v0.3.x rails. Bringing it under the runtime-agnostic architecture means either porting it to use the `persona.yaml` + adapter pattern, or formally deprecating it. (Same applies to `join-collab-project` mode.)
- **Archetype parity in `persona.yaml` + adapters.** The runtime-agnostic spec renders only the `dev` archetype end-to-end. `autonomous-event`, `autonomous-cron`, and `librarian` still live only as legacy `AGENT.md` templates — port them so those archetypes hydrate via `persona.yaml` on each runtime (see `references/persona.schema.md` "Archetype support").
- **Native code-puppy skill packaging.** code-puppy doesn't auto-discover the Claude `SKILL.md` format, so it's invoked by file path today (`USING-WITH-CODE-PUPPY.md`). A native code-puppy skill wrapper would remove the manual step.
- **Cron / failover live wiring.** v1.0 emits cron stubs and failover runbooks but doesn't wire schedulers automatically. Cross-runtime cron auto-registration is real engineering work.
- **Additional adapters** — Codex, Wibey, etc. Add when there's a forcing function (a real project on that runtime).

## How to use this file

- Update on every PR that ships a step.
- New deferred items get added under "v1.1+ candidates."
- Completed items move from `[~]` / `[ ]` to `[x]`.
- Per `CONTRIBUTING.md`, this file is part of every PR that ships a §10 step.
