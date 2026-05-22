# {{PROJECT_NAME}} — Multi-Agent Coordination

## Recent changes
<!-- 3 entries max, most recent first -->

---

## Roles

| Agent | Persona | Workspace | Owns |
|---|---|---|---|
| Iris | Librarian | `{{VAULT_PATH}}` | wiki/, _meta/, _handoff/ triage |
| Dev 1 | Dave | `{{WORKSPACE_BASE}}/[ProjectDev]/` | feature branches, daily dev log |
| Dev 2 *(optional)* | Kris | `{{WORKSPACE_BASE}}/[ProjectDev-2]/` | parallel feature branches |
| Analyst | Vera | `{{WORKSPACE_BASE}}/[ProjectAnalyst]/` | research, GitHub issues |
| Designer | Ivy | `{{WORKSPACE_BASE}}/[ProjectDesigner]/` | content, UX specs |

---

## Session-start checklist

Every agent, every session:

```bash
# 1. Pull vault
git -C {{VAULT_PATH}} pull origin main

# 2. Check open handoffs addressed to you
grep -rl "^status: open" {{VAULT_PATH}}/_handoff/ 2>/dev/null \
  | xargs grep -l "^for: <YourName>\|^for: all" 2>/dev/null

# 3. Read this file (COORDINATION.md) for protocol updates
```

Then: read your workspace CLAUDE.md → pull your repo branch → begin work.

---

## Multi-agent dev rules

- **One branch per agent.** Dave and Kris never work on the same branch simultaneously.
- **No direct commits to `main`.** All changes via PR.
- **PR review:** {{USER_NAME}} reviews and merges all PRs. Agents do not merge their own.
- **Hot files:** if you need to edit one, check the other dev agent's current branch first. Coordinate via handoff if there's a conflict.
- **Scope discipline:** for any ticket touching more than 3 files, a schema migration, or a public module boundary — write the plan in chat and stop for {{USER_NAME}}'s review before writing code.

---

## Hot files

Files that must never have concurrent edits across dev branches:

| File | Why |
|---|---|
| `CLAUDE.md` (repo root) | All agents read this; conflicting edits break everyone's session |
| `COORDINATION.md` | Same |
| `.env.example` | Environment divergence is hard to debug |
| {{HOT_FILES}} | *(add tech-stack-specific hot files here — e.g. schema files, lockfiles)* |

---

## ADR rules

File an ADR when:
- Choosing between two viable technical approaches
- Deciding to break from a pattern established in a prior ADR
- Making an infrastructure or schema change that can't easily be reversed

**Format:** Full ADR lives in the project repo at `docs/adr/ADR-NNN-slug.md`. Vault holds a pointer stub only:

```
projects/{{PROJECT_SLUG}}/decisions/ADR-NNN-slug.md
---
adr: NNN
title: <title>
status: accepted | proposed | superseded
date: YYYY-MM-DD
repo_path: docs/adr/ADR-NNN-slug.md
---
One-sentence summary of the decision.
```

---

## Dev log format

Dev agents write a daily log at:
`projects/{{PROJECT_SLUG}}/ClaudeDevAgent[/ClaudeDevAgent-2]/dev-log/YYYY-MM-DD.md`

Required sections:
- `## Done` — what shipped
- `## Decisions` — non-obvious choices made
- `## Blockers` — anything that stopped progress
- `## Tomorrow` — next planned step

---

## Source-of-truth split

| What | Where |
|---|---|
| Code, migrations, tests | GitHub repo |
| PR state, issue backlog | GitHub |
| Rationale, research, decisions | Vault (`projects/{{PROJECT_SLUG}}/`) |
| Session history, reconciliation | `wiki/log.md` |

GitHub is authoritative for work state. The vault is authoritative for *why*.

---

## Branching

- `main` — production; protected; only {{USER_NAME}} merges here
- `dev` — integration branch; agents target this with PRs (or target `main` directly if no staging layer)
- Feature branches: `<agent>/<ticket-number>-<slug>` (e.g. `dave/123-add-export`)

---

## Ticket lifecycle

1. Vera (or {{USER_NAME}}) opens GitHub issue
2. {{USER_NAME}} assigns to a dev agent (or dev agent self-assigns)
3. Dev agent creates feature branch, opens draft PR when ready for review
4. {{USER_NAME}} reviews, requests changes, or merges
5. Dev agent writes dev-log entry; closes issue via PR description (`Closes #NNN`)

---

## Handoff protocol

**File:** `{{VAULT_PATH}}/_handoff/YYYY-MM-DD-HHMM-<from>-<slug>.md`

**Required frontmatter:**
```yaml
---
created: YYYY-MM-DD
status: open
for: <AgentName | all>
from: <AgentName>
priority: low | medium | high
---
```

**Lifecycle:** receiver reads → acts → sets `status: done`. Never delete handoff files.

---

## Analyst↔dev handoff

When Vera files a GitHub issue for dev:
- Include acceptance criteria and any research links in the issue body
- Drop a handoff `for: Dave` (or `for: Kris`) only if the issue needs verbal context that doesn't fit in the issue

When a dev agent finds that implementation differs from Vera's spec:
- Note the deviation in the dev log
- Drop a handoff `for: Vera` with `priority: medium` describing the deviation

---

## GitHub CLI conventions

Run all GitHub operations from the repo directory:

```bash
gh issue list --state open --limit 50
gh issue create --title "..." --body "..." --label "..."
gh pr create --title "..." --body "..."
gh pr view <number>
```

---

## Conflict resolution

If two agents produce conflicting changes to the same file:
1. Stop — do not force-push
2. Drop a handoff describing the conflict; {{USER_NAME}} resolves it
3. Wait for resolution before continuing on the affected file

---

## What never happens

- `git push --force` to `main` or `dev`
- Using a schema-sync shortcut that bypasses migration files — always use migration files in every environment
- Merging your own PR
- Committing `.env` or secrets to the repo
- Deleting `_handoff/` files
- Writing to `wiki/` from a worker agent (Iris only)
