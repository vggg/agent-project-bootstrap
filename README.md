# agent-project-bootstrap

Scaffolds a multi-agent project setup from templates. **As of v1.0 the pattern is
runtime-agnostic** (per [ADR-001](docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md)):
a single runtime-neutral `persona.yaml` hydrates working personas on whatever AI coding agent
you run — Claude Code, code-puppy, or anything else — at the highest fidelity that runtime
supports. It started as a Claude Code plugin and remains fully compatible with it.

**As of v1.2 this repo ships a sister skill, [`multi-agent-audit`](skills/multi-agent-audit/),** for **grading** multi-agent projects with evidence — INTERVENTION TAX, dual-lens drift, operational fidelity — instead of vibes. Read-only by construction. **v1.3 (2026-06-12)** closed 13 self-review findings from the first real audit + added a timeline view of important events. See [Sister skill](#sister-skill-multi-agent-audit).

Three project modes are available:

- **`vault-project`** — the original lean pattern. Vault-based five-agent project (librarian + two devs + analyst + designer), suitable for solo / local-team work where all collaborators share the same personal vault.
- **`collab-repo-project`** — the **Option A** pattern. Emits a dedicated collab repo per project (CONVENTIONS, COORDINATION, agent manuals, handoffs, decisions, project wiki) separable from any personal vault. Designed for projects with multiple **remote** collaborators who shouldn't have access to each other's personal substrate.
- **`join-collab-project`** — walks a new human collaborator through joining an existing collab repo: clone, claim a persona, set git identity, validate with a "hello" PR.

All emitted files use `{{placeholder}}` tokens you fill once; nothing is hardcoded to a specific project.

## Two generations — which path to use

This repo currently contains **two** scaffolding flows. Knowing which you're on avoids confusion:

- **Runtime-agnostic path (v1.0+, current direction).** Driven by the neutral entrypoints
  `START.md → ORCHESTRATE.md` (set up) / `PARTICIPATE.md` (join), a machine-readable
  `manifest.yaml` + `persona.yaml` per persona, and per-runtime **adapters**. This is what runs
  on **both** Claude Code and code-puppy (see [Runtime support](#runtime-support-v10-runtime-agnostic)
  and [`USING-WITH-CODE-PUPPY.md`](USING-WITH-CODE-PUPPY.md)). The `collab-repo-project` mode below
  is the flow this path generalizes — **for a new multi-runtime or remote-collab project, prefer the
  runtime-agnostic path.**
- **Legacy emit modes (v0.3.x).** The three `{{placeholder}}`-template modes below
  (`vault-project`, `collab-repo-project`, `join-collab-project`) are the original Claude-Code-only
  flows. `vault-project` and `join-collab-project` have **not** yet been ported to the
  runtime-agnostic architecture (tracked in [`STATUS.md`](STATUS.md)); they still emit the
  `AGENT.md`-template world rather than `persona.yaml` + adapters.

If you only run Claude Code and want the simplest thing, the legacy modes still work. If you run
code-puppy (or want enforced Tier-3 guardrails, or multiple runtimes), use the runtime-agnostic path.

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

## Runtime support (v1.0, runtime-agnostic)

Personas are defined once in a runtime-neutral `persona.yaml` (identity, abstract
*capabilities*, scope, session ritual). Each runtime maps those abstract capabilities onto its
real tools via an **adapter** — the only runtime-specific surface. Adding a runtime means
adding an `adapters/<runtime>/` folder and touching nothing else.

A persona always runs at the highest tier its runtime supports (the **capability ladder**),
and degrades gracefully:

| Tier | Runtime | Mechanism | Enforcement |
|---|---|---|---|
| 3 | **Claude Code (v1.1)** or code-puppy | native sub-agents (Claude `.claude/agents/<slug>.md`; code-puppy JSON agents) | capabilities enforced via a tool allow-list — **whole-tool denials are real** (a read-only persona genuinely cannot write/run shell); sub-tool denials instructed |
| 2 | Claude Code | persistent `CLAUDE.md` | persistent session context; capabilities instructed |
| 1 | anything | in-prompt | persona re-read each turn; self-enforced |

> **New in v1.1:** the Claude adapter renders **either** Tier 2 (`CLAUDE.md`) **or** Tier 3
> (a native subagent with an enforced tool allow-list), selected by a runtime-neutral
> `adapters.claude.tier` config (`auto` | `2` | `3`, default `auto`; `auto` uses Tier 3 when the
> session can host subagents and falls back to Tier 2 otherwise). So enforced guardrails are no
> longer code-puppy-only.

Key files:

- `START.md` / `ORCHESTRATE.md` / `PARTICIPATE.md` — neutral entrypoints (front door + the two
  role recipes; routing is by directory state, not a human choice).
- `adapters/{generic,code-puppy,claude}/HYDRATE.md` — per-runtime mappings (`generic` is the
  mandatory Tier-1 fallback).
- `references/{capability-vocab.v1,persona.schema,manifest.schema}.md` — the canonical spec.

See [ADR-001](docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md) for the full design.

## Sister skill — `multi-agent-audit`

The other half of the kit: a **read-only audit skill** that grades multi-agent projects against an evidence-based rubric. Bootstrap **builds** projects; audit **grades** them.

| Property | Detail |
|---|---|
| **Location** | [`skills/multi-agent-audit/`](skills/multi-agent-audit/) |
| **Headline metric** | INTERVENTION TAX = human touches per autonomous task. High autonomy split + high tax = false win. |
| **Read-only** | Never modifies the audited project. Tool allow-list omits `Edit`; `Write` only for the report, outside the audited repos. |
| **Framework-neutral** | Works on `agent-project-bootstrap`, CrewAI, LangGraph, AutoGen, Copilot agents, custom loops. |
| **Two-layer** | Universal WHAT-to-measure + per-layout WHERE-it-lives discovery (Step 0). |
| **Outputs** | Markdown report + self-contained HTML dashboard (Chart.js + horizontal SVG timeline) + 1 KB short-form executive summary (md or html) + machine-readable snapshot JSON for trend analysis. |
| **v1.3 enhancements** | Multi-substrate Agents lens (claim labels + handoffs + frontmatter, not just git log); snapshot `addenda:` field for revising shipped point-in-time records; weighted operational-fidelity option; 5 stdlib Python helpers (trend reader, timeline extractor, Brandes' betweenness centrality, coverage parsers, per-persona PR attribution); HTML renderer + short-form renderer; subagent-isolation smoke test + automated contract checker. |

Invoke via the bundled `project-auditor` subagent (`skills/multi-agent-audit/agents/project-auditor.md`) which enforces the read-only rule at the tool layer, or read `SKILL.md` directly from any runtime.

Full workflow: Discovery → Agent Inventory + DUAL-LENS drift pass → Metrics mining (platform, not just git) → 1–5 axis scoring → Markdown/HTML report → snapshot persistence (trend mode kicks in once ≥2 snapshots exist).

## Installation

```
/plugin install https://github.com/vggg/agent-project-bootstrap   # from GitHub
/plugin install /path/to/agent-project-bootstrap                  # from a local clone (e.g. for development)
```

> The `/plugin install` command syntax may evolve as Claude Code matures. If the above fails, check the [Claude Code docs](https://docs.anthropic.com/claude-code) for the current install command format.

> **On code-puppy?** It doesn't auto-discover the Claude skill format — see
> [`USING-WITH-CODE-PUPPY.md`](USING-WITH-CODE-PUPPY.md) for the invoke-by-file-path quickstart.

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
