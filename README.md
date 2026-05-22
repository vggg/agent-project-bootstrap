# agent-project-bootstrap

A Claude Code plugin that scaffolds a multi-agent project setup from templates. It generates the Obsidian vault structure for a librarian agent (Iris), the COORDINATION.md that governs cross-agent protocol, and the workspace CLAUDE.md files for up to four worker agents: two developers, an analyst, and a designer. All files use `{{placeholder}}` tokens you fill once; nothing is hardcoded to a specific project.

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

## Installation

```
/plugin install https://github.com/vggg/agent-project-bootstrap
```

> The `/plugin install` command syntax may evolve as Claude Code matures. If the above fails, check the [Claude Code docs](https://docs.anthropic.com/claude-code) for the current install command format.

## Usage

After installation, tell Claude something like:

> "Use the agent-project-bootstrap skill to set up a new project."

Claude will ask for your project name, vault path, workspace base directory, GitHub repo, live URL, and tech stack, then emit all files with placeholders substituted. The emit process is documented in `skills/agent-project-bootstrap/SKILL.md` for reference.

## Customisation

The templates use archetype names for agents (Iris, Dave, Kris, Vera, Ivy). These are just names — rename them to whatever fits your working style. The structural patterns (three-tier write ownership, handoff protocol, COORDINATION.md as single source for cross-agent rules) are what carry the value, not the names themselves.

The dev-2 slot (Kris) is explicitly optional. Single-developer projects skip it.

## Acknowledgements

This skill codifies a multi-agent coordination pattern developed through real iteration on a software project. The goal is to make the setup repeatable without requiring each new project to rediscover the same structural decisions.

---

MIT License · [vggg](https://github.com/vggg)
