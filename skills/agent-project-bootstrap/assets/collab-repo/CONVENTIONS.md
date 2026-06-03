# {{PROJECT_NAME}} — Conventions

Project-wide conventions that apply to every persona on the team. These are the rules of the road. Read once; reference when needed.

## Recent changes

<!-- 3 entries max, most recent first -->

---

## Repo split

| Repo | Owns | Your access |
|---|---|---|
| `{{CODE_REPO}}` | Application code, migrations, tests, PR/issue work state | Per persona (see your `agents/<you>/AGENT.md`) |
| `{{COLLAB_REPO}}` (this repo) | Persona manuals, conventions, coordination, decisions, findings, wiki | Per persona — typically write-via-PR for collaborators during trust-gating; direct push afterward |

GitHub is authoritative for **work state** (issues, PRs, merges). This repo is authoritative for **why** (decisions, findings, conventions).

---

## Identity, labels, and routing

Each persona has a row in this table. The project owner assigns persona slots to humans (one human → one or more personas).

| Persona | GitHub handle | Git identity | Commit prefix | Routing label |
|---|---|---|---|---|
| {{OWNER_HANDLE}} (owner) | `@{{OWNER_HANDLE}}` | (real human identity) | n/a (uses persona prefixes when running an agent) | `@{{OWNER_HANDLE}}` direct |
| (one row per persona — fill from `agents/<persona>/AGENT.md`) | | | | |

**Routing convention:**
- Autonomous personas (PR Reviewer, Backtest Runner, Librarian, etc.) **do not have GitHub accounts**. Tag them via the `agent-<persona>` label on the relevant issue or PR. The persona's session-start grep picks it up.
- Human collaborators **do** have GitHub accounts and can be `@`-tagged. Prefer the label-routing convention for async asks (more durable than @-mentions); reserve `@`-tag for "I need a synchronous response from this specific human."

---

## Wikilinks and file references

Use wikilinks (`[[folder/filename]]`) for vault-internal references between files in this repo. Use Markdown links (`[label](path)`) for GitHub-rendered display (READMEs, PR descriptions).

---

## Capabilities, not tool names

Work in this repo is described as abstract CAPABILITIES, never a specific runtime's tools.
Your runtime maps each capability to concrete tools via `adapters/<runtime>/HYDRATE.md`.

| Task | Capability |
|---|---|
| Read or write a file | `read_*` / `write_*` (see `references/capability-vocab.v1.md`) |
| Search content | covered by `read_code` / `read_collab` |
| Git operations | sub-tool of the runtime's shell capability |
| Work-state (issues, PRs) | `open_pr` and the project's backlog source (see `manifest.yaml`) |

The repo is a plain Markdown filesystem — it does not depend on any runtime's vault plugin or
integration layer. If your runtime offers such integrations, that is an adapter detail, not a
project convention.

---

## `_handoff/` lifecycle

All cross-persona async messages go through `_handoff/`. Filename: `YYYY-MM-DD-HHMM-<from>-<topic-slug>.md`.

Required frontmatter:
```yaml
---
created: YYYY-MM-DD
status: open
for: <PersonaName | all>
from: <PersonaName>
priority: low | medium | high
---
```

**Lifecycle:** receiver reads → acts → sets `status: done`. **Never delete handoff files.** The append-only model preserves coordination history.

**Push policy:** `_handoff/` files (both creation and status-flip) **may be direct-pushed to `main`** — they're coordination metadata, not substantive changes. Substantive changes (code, persona `AGENT.md` edits, `decisions/`, `CONVENTIONS.md`, `COORDINATION.md`, `wiki/` entries authored by the Librarian) require a PR per each persona's working rules. This exception keeps the coordination surface cheap; the PR gate stays on the things that benefit from review.

---

## Contradictory rules

If two documents in this repo contradict each other, the precedence order is:

1. `CONVENTIONS.md` (this file) — vault mechanics + repo-wide rules
2. `COORDINATION.md` — multi-persona protocol + workflow
3. Persona `AGENT.md` — persona-specific rules

If you find a contradiction, drop a `_handoff/` for the owner (`for: {{OWNER_HANDLE}}`) describing the conflict. Don't auto-fix shared config.

---

## What never happens

- `git push --force` to `main` on either repo
- Deleting `_handoff/` files
- Writing to `wiki/` from a non-Librarian persona
- Committing secrets (`.env`, credentials, API keys)
- A persona acting outside the scope declared in its `AGENT.md`
