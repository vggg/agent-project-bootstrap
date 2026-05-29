# agent-project-bootstrap

A Claude Code plugin that scaffolds a multi-agent project setup from templates. As of **v0.3.0**, three modes are available:

- **`vault-project`** — the original lean pattern. Vault-based five-agent project (librarian + two devs + analyst + designer), suitable for solo / local-team work where all collaborators share the same personal vault.
- **`collab-repo-project`** — the **Option A** pattern. Emits a dedicated collab repo per project (CONVENTIONS, COORDINATION, agent manuals, handoffs, decisions, project wiki) separable from any personal vault. Designed for projects with multiple **remote** collaborators who shouldn't have access to each other's personal substrate.
- **`join-collab-project`** — walks a new human collaborator through joining an existing collab repo: clone, claim a persona, set git identity, validate with a "hello" PR.

All emitted files use `{{placeholder}}` tokens you fill once; nothing is hardcoded to a specific project.

## When it's useful

- You're running multiple Claude Code sessions in parallel on the same long-lived project
- You want a knowledge layer (research findings, decisions, reconciliation log) that lives separate from the codebase
- You're a solo or near-solo developer who coordinates with several specialist agents rather than a human team
- You've used multi-agent Claude Code before and want a repeatable starting point instead of rebuilding config files from scratch each time

## When it's overkill

- One-shot or throwaway tasks (a single agent session is simpler)
- Projects where you don't need persistent memory across sessions
- Team setups where human engineers handle coordination and you only need one agent at a time

## What gets generated

### `vault-project` mode

**Vault structure** (Obsidian, git-tracked):
```
_meta/
  CONVENTIONS.md          # tool hierarchy + wikilinks rules
  PERSONAS/
    IRIS.md               # librarian role definition
    DAVE.md               # dev agent 1
    KRIS.md               # dev agent 2 (optional)
    VERA.md               # analyst
    IVY.md                # designer
CLAUDE.md                 # Iris session guide
projects/<project>/
  CLAUDE.md               # project brief (open threads, key decisions)
  COORDINATION.md         # cross-agent protocol (handoffs, ADRs, dev log, branching)
```

**Workspace files** (one per agent, checked into their respective repos or directories):
```
workspaces/
  dev/CLAUDE.md           # engineering guide (used by both dev agents)
  analyst/CLAUDE.md       # analyst session guide
  designer/CLAUDE.md      # designer session guide
```

### `collab-repo-project` mode (new in v0.3.0)

**Collab repo structure** (a dedicated GitHub repo, separate from your code repo):
```
README.md                 # project overview
CONVENTIONS.md            # repo-wide rules (identity, labels, routing, tool hierarchy)
COORDINATION.md           # multi-persona protocol + Hot files section
CLAUDE.md                 # entry pointer for any Claude Code session
BOOTSTRAP.md              # collaborator-facing onboarding
BOOTSTRAP-ADMIN.md        # owner-only operations (optional trust-gating runbook)
agents/
  <persona-slug>/
    AGENT.md              # per-persona operating manual
  librarian/
    AGENT.md              # always emitted by default
    FAILOVER.md           # centralized-with-failover runbook
_handoff/                 # cross-persona async messages
decisions/                # project-level decisions + ADR pointer stubs
findings/                 # investigations, dev logs, UAT, research
wiki/                     # synthesised by the Librarian
```

Three persona archetypes are supported, distinguished by runtime:
- **dev** — human-triggered Claude Code sessions on the collaborator's machine
- **autonomous-event** — GitHub Actions on a webhook (e.g. PR Reviewer, Backtest Runner)
- **autonomous-cron** — `/schedule` skill on someone's machine (e.g. PM+UAT, Librarian)

### Slash commands (both modes)

**Slash commands** (installed globally, available to every Claude Code session):
```
commands/
  vc.md                   # `/vc` — vault commit workflow with agent-prefix convention
```

## Installation

```
/plugin install https://github.com/vggg/agent-project-bootstrap
```

> The `/plugin install` command syntax may evolve as Claude Code matures. If the above fails, check the [Claude Code docs](https://docs.anthropic.com/claude-code) for the current install command format.

## Usage

After installation, tell Claude something like:

> "Use the agent-project-bootstrap skill to set up a new project in `collab-repo-project` mode."

Claude will ask for the inputs the mode needs (project name, repos, personas, etc.) and emit all files with placeholders substituted. Each mode is self-contained — `SKILL.md` has a section per mode you can read independently.

**Choosing a mode:**
- Use `vault-project` if you're the only operator (or all collaborators share your vault) and want the simplest setup.
- Use `collab-repo-project` if multiple remote collaborators need to see each other's work and you want trust isolation between them and your personal substrate.
- Use `join-collab-project` if you're a new collaborator joining a project someone else set up.

## Customisation

The templates use archetype names for agents (Iris, Dave, Kris, Vera, Ivy). These are just names — rename them to whatever fits your working style. The structural patterns (three-tier write ownership, handoff protocol, COORDINATION.md as single source for cross-agent rules) are what carry the value, not the names themselves.

The dev-2 slot (Kris) is explicitly optional. Single-developer projects skip it.

## Acknowledgements

This skill codifies a multi-agent coordination pattern developed through real iteration on a software project. The goal is to make the setup repeatable without requiring each new project to rediscover the same structural decisions.

---

MIT License · [vggg](https://github.com/vggg)
