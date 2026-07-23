# STATUS — agent-project-bootstrap

Tracks current progress and deferred candidates. Update on every PR that ships a step (per
`CONTRIBUTING.md`). Full release history lives in `CHANGELOG.md`; the v0→v1 migration story
lives in [`docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md`](docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md).

## In progress — Phase 2: conventions → mechanisms (baron CLI)

Per [ADR-003](docs/adr/ADR-003-baron-cli.md): the coordination conventions ADR-002 promoted
are being mechanized as the `baron` CLI (`cli/`, typer+pyyaml only, markdown/git substrate
stays the only database). Unreleased — see `CHANGELOG.md` [Unreleased].

- [x] **M1 `baron validate`** — schema validation for persona.yaml/manifest.yaml; frozen
  10-verb vocabulary embedded + drift-guarded against `capability-vocab.v1.md`.
- [x] **M2 `baron status`** — divergence/staleness report (the 2026-07-22 stranding classes,
  handoff SLA, ledger/wiki staleness); `workspace.*` manifest fields (schema v1.2).
- [x] **M3 ledgers/handoffs/index** — push-retry F/D allocation, handoff lifecycle with
  archive-not-delete, marker-delimited `_handoff/README.md` index.
- [ ] **M4+ forge-consuming commands** (lock guard, merger preconditions) — `docs/BACKLOG.md`.
- [ ] **M6 worktree/branch-per-persona topology** — `docs/BACKLOG.md`.

## Shipped

| Version | Date | Summary (details in `CHANGELOG.md`) |
|---|---|---|
| **v1.4.0** | 2026-07-22 | One front door + legacy quarantine + July-2026 ways-of-working (ADR-002) + archetype parity + real CI. See below. |
| v1.3.0 | 2026-06-12 | `multi-agent-audit` v1.3 — closed all 13 first-real-audit findings + timeline feature. |
| v1.2.0 | 2026-06-12 | `multi-agent-audit` sister skill + `project-auditor` subagent. |
| v1.1.x | 2026-06-04/08 | Claude Tier-3 subagent rendering; docs reconciled to the runtime-agnostic architecture. |
| v1.0.x | 2026-06-03 | The runtime-agnostic milestone (ADR-001 §10 executed; all close-out items done). |

## v1.4.0 — shipped 2026-07-22

The credibility-debt release: one front door, honest artifacts, real tests.

- [x] **One front door.** `SKILL.md` is now a thin router to `assets/collab-repo/START.md`
  (→ `ORCHESTRATE.md` / `PARTICIPATE.md`). The legacy v0.3 emit path (`vault-project` +
  `workspaces` templates, three-mode emit instructions) is quarantined in `legacy/` —
  deprecated, unmaintained, kept for existing projects.
- [x] **Version coherence.** `plugin.json` ≡ `SKILL.md` frontmatter (1.4.0), enforced by
  `tests/lint_repo.py`; stale "v1.0 shipped" meta-docs corrected.
- [x] **Archetype parity (closes the ADR-001 §10.8 deferred item).** `persona.yaml` templates
  now exist for `librarian`, `__AUTONOMOUS_EVENT__`, and `__AUTONOMOUS_CRON__` alongside
  their `AGENT.md`s; `persona.schema.md`'s legacy-only caveat removed.
- [x] **Missing artifacts.** `assets/collab-repo/manifest.example.yaml` (worked example);
  `__DEV__/persona.yaml` is a real `{{...}}` template (was a verbatim copy of the tess test
  fixture); `docs/notes/{CORRECTION-wibey-vs-codepuppy,code-puppy-capability-map}.md`
  reconstructed so the spec's citations resolve.
- [x] **July-2026 ways-of-working (ADR-002).** Single-account constraint as first principle;
  "everything material gets a handoff"; lock-via-open-PR + CI guard (not CODEOWNERS);
  adversarial Reviewer + Merger persona templates (`__REVIEWER__`, `__MERGER__`) with
  SHA-bound verdicts; persona.yaml CI validation; machine-local agent-state convention.
  Folded into the emitted `CONVENTIONS.md` / `COORDINATION.md`.
- [x] **Real tests + CI.** `tests/bi_runtime_accept.py` now parses the adapters' actual
  machine-readable capability maps (was a tautological Python re-implementation);
  `tests/lint_repo.py` (placeholders, dead links, fixture leaks, version sync);
  `.github/workflows/ci.yml` runs both with plain python on push + PR.

## Deferred candidates

### agent-project-bootstrap

- **Native code-puppy skill packaging.** code-puppy doesn't auto-discover the Claude
  `SKILL.md` format, so it's invoked by file path today (`USING-WITH-CODE-PUPPY.md`).
- **Cron / failover live wiring.** The templates emit cron stubs and failover runbooks but
  don't wire schedulers automatically; cross-runtime cron auto-registration is real
  engineering work.
- **Additional adapters** — Codex, Wibey, etc. Add when there's a forcing function (a real
  project on that runtime).
- **Template CI emission.** ADR-002 §3/§5 describe the lock-guard Action and persona.yaml
  validation a bootstrapped project should run; ORCHESTRATE could emit a ready-made
  `.github/workflows/` for them.
- **Vault-project modernization.** The lean personal-vault pattern now lives only in
  `legacy/`; if demand returns, re-derive it on the runtime-agnostic architecture rather
  than reviving the v0.3 rails.

### multi-agent-audit

- **Per-runtime adapter docs** for non-bootstrap layouts (CrewAI / LangGraph / AutoGen /
  Copilot agents) — dedicated `references/<runtime>-adapter.md` files when a real audit
  demands them.
- **Sub-tool scoping for `Bash`** in `project-auditor.md` once Claude Code supports it —
  would harden the read-only contract from instruction-enforced to tool-enforced.
- **Weekly throughput histogram** in the snapshot schema.
- **`coverage.py` binary `.coverage` parser**; **native Go cover profile parser**.
- **Trend-mode auto-trigger** from `render_report.py`.
- **HTML email-friendly compact mode** for digest distribution.

## How to use this file

- Update on every PR that ships a step.
- New deferred items get added under "Deferred candidates."
- Completed items move into the current release section with `[x]`.
- Per `CONTRIBUTING.md`, this file is part of every PR that ships a tracked step.
