# agent-project-bootstrap — Repo Guide

## What this repo is

The **canonical home** for the `agent-project-bootstrap` skill. As of ADR-001 acceptance (2026-05-30) and the v1.0.0 release (2026-06-03), this repo is also the active **development surface** — the runtime-agnostic spec, adapters, references, tests, and meta-docs all live and evolve here.

Current state: v1.0 shipped. Track `STATUS.md` for v1.0 close-out items and v1.1 candidates.

## Canonicality (v1.0 onward)

This repo is canonical for everything. The earlier "vault is canonical, repo is a release snapshot between releases" rule (v0.x convention) is **sunset** as of v1.0.

| Surface | Canonical home |
|---|---|
| ADRs (`docs/adr/`) | this repo |
| Runtime adapters (`skills/agent-project-bootstrap/assets/collab-repo/adapters/{claude,code-puppy,generic}/`) | this repo |
| Canonical spec (`skills/agent-project-bootstrap/references/`) | this repo |
| Acceptance tests (`tests/`) | this repo |
| Emit-time templates (everything else under `skills/agent-project-bootstrap/assets/`) | this repo |
| Meta-docs (`README.md`, `CLAUDE.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `STATUS.md`) | this repo |
| `.claude-plugin/plugin.json` | this repo (bumped at release) |

The vault retains a historical copy under `_meta/skills/agent-project-bootstrap/`; treat it as archival reference, not a source of truth.

## Persona / role for a fresh agent

A fresh Claude Code (or code-puppy, or any other) session landing in this repo operates as a **generic dev archetype**. This repo does not yet dogfood its own multi-persona pattern — there is no `CONVENTIONS.md` / `COORDINATION.md` / `agents/` at the *repo root*. Vikram works directly with the agent as a single dev. Persona-routing labels (`agent-<name>`) are not defined for this repo.

The `CONVENTIONS.md` and `COORDINATION.md` files you'll see under `skills/agent-project-bootstrap/assets/collab-repo/` are **emit-time templates** that get copied into projects scaffolded BY this skill — they are not this repo's own convention files.

## Repo layout

```
.claude-plugin/
  plugin.json             # plugin manifest — version number lives here
skills/
  agent-project-bootstrap/
    SKILL.md              # Claude-facing emit instructions
    references/           # canonical spec
      capability-vocab.v1.md
      persona.schema.md
      manifest.schema.md
      collab-repo-design.md
      design-decisions.md
      obsidian-setup.md
    assets/
      collab-repo/
        START.md, ORCHESTRATE.md, PARTICIPATE.md   # neutral entrypoints (v1.0)
        adapters/
          claude/, code-puppy/, generic/           # runtime adapters (each has HYDRATE.md)
        agents/
          __DEV__/, __AUTONOMOUS_EVENT__/, __AUTONOMOUS_CRON__/, librarian/
        CONVENTIONS.md, COORDINATION.md, CLAUDE.md, BOOTSTRAP.md,
        BOOTSTRAP-ADMIN.md, QUICKSTART.md, README.md,
        _handoff/, decisions/, findings/, wiki/, workspace-template/,
        _failover-cron-sections/
      vault/              # vault-project mode templates
      workspaces/         # workspace CLAUDE.md templates
      commands/           # slash command templates (e.g. vc.md)
docs/
  adr/                    # architecture decision records (ADR-001 et seq.)
tests/
  bi_runtime_accept.py    # bi-runtime acceptance harness
  examples/               # example persona fixtures (rex, tess)
CHANGELOG.md
CLAUDE.md                 # this file
CONTRIBUTING.md           # PR conventions incl. "docs land with code" rule
LICENSE
README.md
STATUS.md                 # v1.0 close-out + v1.1 progress tracker
```

## Versioning

Semver. Patch (0.0.x): wording fixes, typos, broken references. Minor (0.x.0): new placeholders, new template sections, structural improvements. Major (x.0.0): breaking changes to the emit process or file layout.

v1.0.0 (2026-06-03) is the runtime-agnostic milestone. **v1.1 adds Claude Tier-3 subagent rendering** (the Claude adapter now renders either Tier 2 `CLAUDE.md` or a Tier-3 native subagent with an enforced `tools:` allow-list, selected by the runtime-neutral `adapters.claude.tier` config). v1.1+ continues to track the remaining ADR-001 §10.8 deferred items (vault-project re-integration, cron/failover live wiring, additional adapters) and v1.0 close-out work.

## Release workflow

```bash
# 1. Verify the bi-runtime acceptance test passes:
uv run --with pyyaml python tests/bi_runtime_accept.py

# 2. Bump version in .claude-plugin/plugin.json
# 3. Move [Unreleased] content in CHANGELOG.md to a new version section

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

**Bi-runtime acceptance test** — the gate for adapter / spec / canonical-contract changes:
```bash
uv run --with pyyaml python tests/bi_runtime_accept.py
```
(The harness needs PyYAML; `uv run --with pyyaml` provides it without a global install.)

Validates that one `persona.yaml` hydrates to an equivalent behavior contract on both Claude Code and code-puppy adapters. Run before any PR touching adapters, references, or the v1.0 canonical contract files.

## PR rules

See `CONTRIBUTING.md`. Key rule (post-2026-06-03): **documentation lands with code in the same PR** — never as a follow-up. Affected ADRs, `CLAUDE.md`, `README.md`, `CHANGELOG.md`, and `STATUS.md` updates are all part of "done."

## See also

- `STATUS.md` — v1.0 close-out items + v1.1 progress
- `docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md` — the accepted v1.0 architecture
- `CONTRIBUTING.md` — PR conventions including the docs-with-code rule
- `README.md` — user-facing description of the skill
