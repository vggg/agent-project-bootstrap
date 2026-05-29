# {{PROJECT_NAME}} — Bootstrap

Welcome. This walks you through joining {{PROJECT_NAME}} as a remote collaborator. Plan for 30–60 minutes the first time.

## What this project is

{{PROJECT_DESCRIPTION}}

The project runs as a small distributed team. Each collaborator (you) operates one or more *personas* — durable team identities backed by their own git config, ticket label, and operating manual. The team coordinates async via two GitHub repos:

- **Code repo** ([`{{CODE_REPO}}`](https://github.com/{{CODE_REPO}})) — the application code, PRs, issues.
- **Collab repo** ([`{{COLLAB_REPO}}`](https://github.com/{{COLLAB_REPO}}), this one) — persona manuals, conventions, coordination, decisions, findings, the project wiki.

## The team

| Role | Persona | GitHub | Owns |
|---|---|---|---|
| Project owner | {{USER_NAME}} | `@{{OWNER_HANDLE}}` | Final calls, cross-cutting decisions |
| (one row per persona — fill from `agents/<persona>/AGENT.md`) | | | |

**Important:** autonomous personas (PR Reviewer, Backtest Runner, Librarian, etc.) do **not** have their own GitHub accounts. They run as automation (GitHub Actions, scheduled cron) and you communicate with them via `agent-<persona>` labels on issues/PRs. Only humans get `@`-tagged.

## Step 1 — pick (or claim) your persona

Look in `agents/` for available persona slots. Each subfolder is a persona that's either:
- **Assigned** to a specific human (see the persona's `AGENT.md` frontmatter `assigned_to` field)
- **Unassigned** — available to claim

If the project owner has already told you which persona to take, use that. Otherwise, drop a `_handoff/` for `@{{OWNER_HANDLE}}` asking for an assignment.

## Step 2 — read your persona's AGENT.md

Your persona's `AGENT.md` (at `agents/<your-persona>/AGENT.md`) tells you:
- Your git identity (name + email)
- Your ticket label
- Your commit message prefix
- Your workspace path (where to clone the code repo locally)
- Your session-start ritual
- Your ADR rules
- Your end-of-session ritual

**Read it end-to-end before doing anything else.**

## Step 3 — set git identity

In your local clone of *this* repo, set the per-repo git config matching your persona's identity:

```bash
git config user.name "<your persona name>"
git config user.email "<your persona email>"
```

Repeat in your local clone of the code repo once you've cloned it.

This per-repo override means your other Git work (personal projects, employer repos) keeps your real identity. {{PROJECT_NAME}} commits land under your persona.

## Step 4 — clone the code repo

```bash
git clone git@github.com:{{CODE_REPO}}.git <your workspace path per your AGENT.md>
cd <workspace>
git config user.name "<your persona name>"
git config user.email "<your persona email>"
```

## Step 5 — read the rest of the orientation set

In order:

1. `CONVENTIONS.md` (this repo) — repo-wide rules
2. `COORDINATION.md` (this repo) — multi-persona protocol, session-start checklist, hot files
3. `wiki/log.md` (this repo) — recent project activity, what's in flight

## Step 6 — open your first PR

Pick a small, low-stakes ticket from the code repo (or just open a "Hello, I'm <persona>" trivial PR — add a comment to the README or fix a typo). The point is to validate the round trip end-to-end: branch, push, PR, review, merge.

```bash
# In your code repo workspace:
git checkout -b chore/hello-<your-persona>
# (make a tiny edit)
git add .
git commit -m "<your-prefix>: hello — <persona> joins the team"
git push -u origin chore/hello-<your-persona>
gh pr create --title "<your-prefix>: hello" --body "Validating round trip per BOOTSTRAP.md step 6."
```

Tag `@{{OWNER_HANDLE}}` in the PR description. Once they merge, you're operational.

## Bootstrap checklist

```
[ ] Accept GitHub collaborator invites (this repo + code repo)
[ ] Pick / claim a persona (see Step 1)
[ ] Read your agents/<persona>/AGENT.md end-to-end
[ ] git clone this repo + set git identity per AGENT.md
[ ] git clone the code repo + set git identity per AGENT.md
[ ] Read CONVENTIONS.md, COORDINATION.md, wiki/log.md
[ ] Open your first "hello" PR and get it merged
[ ] Drop a handoff to the Librarian (for: librarian) announcing you've joined so the wiki gets updated
```

When you hit your first blocker or question, drop a `_handoff/` or open a GitHub issue with the right `agent-*` label. Don't sit on it.

Welcome aboard.
