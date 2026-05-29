# {{PROJECT_NAME}} — Multi-Persona Coordination

How the personas on this project coordinate work. Read at session start.

## Recent changes

<!-- 3 entries max, most recent first -->

---

## Personas at a glance

| Persona | Archetype | Owns |
|---|---|---|
| (one row per persona — fill from `agents/<persona>/AGENT.md`) | dev / autonomous-event / autonomous-cron / librarian | |

Full operating manuals: `agents/<persona>/AGENT.md`.

---

## Session-start checklist

Every persona, every session:

1. **Pull both repos:**
   ```bash
   git -C {{LOCAL_COLLAB_PATH}} pull origin main
   git -C {{LOCAL_CODE_PATH}} pull origin main   # if you have code-repo write access
   ```
2. **Read your persona's `agents/<you>/AGENT.md`** for any updates.
3. **Check open handoffs addressed to you:**
   ```bash
   grep -rl "^status: open" {{LOCAL_COLLAB_PATH}}/_handoff/ 2>/dev/null \
     | xargs grep -l "^for: <YourPersona>\|^for: all" 2>/dev/null
   ```
4. **Read open work assigned to you on the code repo:**
   ```bash
   gh issue list --state open --label agent-<you> --repo {{CODE_REPO}}
   gh issue list --state open --label agent-<you> --repo {{COLLAB_REPO}}
   ```
5. **Read this file (`COORDINATION.md`)** for protocol updates.

Then: begin work.

---

## Multi-persona dev rules

- **One branch per active task.** Don't open parallel branches against the same files.
- **No direct commits to `main`** on the code repo. All changes via PR.
- **PR review:** code repo PRs are reviewed per the project's review policy (see `BOOTSTRAP-ADMIN.md`); collab repo PRs go through {{OWNER_HANDLE}} during initial trust window if active.
- **Scope discipline:** for any ticket touching more than 3 files, a schema migration, or a public module boundary — write the plan in chat and stop for {{OWNER_HANDLE}}'s review before writing code.

---

## Hot files

Files that need coordination across personas. Pattern vocabulary:

- **Separation** — file is split per-persona; no shared write target. No coordination needed.
- **Owner** — single persona is the gatekeeper. Others file tickets to change.
- **Lock** — labels claim exclusive edit access. Release on merge or after 24h soft timeout.

Hot files for this project:

| File / glob | Pattern | Owner / Lock label | Notes |
|---|---|---|---|
| `CONVENTIONS.md` (this repo) | Owner | {{OWNER_HANDLE}} | Project rules; rare changes; file ticket |
| `COORDINATION.md` (this repo) | Owner | {{OWNER_HANDLE}} | Same |
| `agents/<persona>/AGENT.md` | Owner | that persona (or {{OWNER_HANDLE}}) | Persona's own manual |
| `wiki/log.md`, `wiki/*` | Owner | Librarian | Only the Librarian writes here |
| {{HOT_FILES_TABLE_ROWS}} | | | *(add tech-stack-specific hot files here — e.g. schema files, lockfiles)* |

**Label-lock mechanics:**
1. Claim by adding the lock label to the issue/PR.
2. Release on merge automatically, or on close explicitly.
3. 24-hour soft timeout — anyone may ping the holder; release after 4h non-response if held longer than 24h.

If a project routinely hits the timeout, refactor toward architectural separation.

---

## ADR rules

File an ADR when:
- Choosing between two viable technical approaches
- Deciding to break from a pattern established in a prior ADR
- Making an infrastructure or schema change that can't easily be reversed

**Format:** Full ADR lives in the code repo at `docs/adr/ADR-NNN-slug.md`. This collab repo holds a pointer stub:

```markdown
projects/decisions/ADR-NNN-slug.md
---
adr: NNN
title: <title>
status: accepted | proposed | superseded
date: YYYY-MM-DD
repo_path: docs/adr/ADR-NNN-slug.md
---
One-sentence summary of the decision.
```

Project-level (non-architectural) decisions live in `decisions/YYYY-MM-DD-HHMM-slug.md` with their full content — no code-repo pointer.

---

## Branching (code repo)

- `main` — production; protected; reviewed merges only
- Feature branches: `<persona>/<ticket-number>-<slug>` (e.g. `dave/123-add-export`)
- Rebase on `main` before opening a PR
- Use `Closes #N` in PR body to auto-close issues on merge

---

## Ticket lifecycle (code repo)

1. Analyst (or any persona) opens a GitHub issue with title, context, acceptance criteria, and label
2. Persona self-assigns via `gh issue edit <N> --add-assignee "@me" --add-label "agent-<self>"`
3. Persona creates feature branch, opens PR when ready
4. Per-project review policy decides who approves and merges
5. Persona writes dev-log entry; closes issue via PR description

---

## Async handoff protocol

GitHub comments are for code discussion. Cross-persona coordination — task handoffs, blocking questions, completed subtask notifications, requests for input — go through `_handoff/`. See `CONVENTIONS.md § _handoff/ lifecycle` for format.

**Iris (project owner's personal librarian) extension:**
If the project owner runs an Iris persona on their personal machine in addition to this project, they can address handoffs `for: Iris` from this repo. Iris's session-start grep extends to read this repo's `_handoff/` for items addressed to her. One-way visibility — this repo doesn't see the personal vault.

---

## Conflict resolution

If two personas produce conflicting changes to the same file:
1. Stop — do not force-push
2. Drop a handoff describing the conflict; {{OWNER_HANDLE}} resolves it
3. Wait for resolution before continuing on the affected file

---

## What never happens

- A non-Librarian persona writes to `wiki/`
- A persona acts outside the scope declared in its `AGENT.md`
- Merging a PR that touches another persona's owner-locked files without that persona's approval
- Skipping a label lock on `Lock`-pattern hot files

---

## Source-of-truth split

| What | Where |
|---|---|
| Code, migrations, tests | `{{CODE_REPO}}` |
| PR state, issue backlog | GitHub (both repos) |
| Rationale, research, decisions | This repo (`{{COLLAB_REPO}}`) |
| Session history, reconciliation | `wiki/log.md` in this repo |
