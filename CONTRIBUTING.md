# Contributing

## Scope

Refinements to the multi-agent pattern emitted by this skill are welcome. Pattern evolution is governed by the ADR process (`docs/adr/`); see [ADR-001](docs/adr/ADR-001-runtime-agnostic-multi-agent-bootstrap.md) for the v1.0 direction (runtime-agnostic spec + adapters for Claude Code, code-puppy, and a generic Tier-1 fallback).

If you want to explore a fundamentally different vault integration (e.g. non-Obsidian), fork this and publish a separate skill rather than expanding this one's scope.

## Before opening a PR

Open an issue first describing what you want to change and why. Small fixes (typos, broken links, minor wording) don't need an issue.

## How to test

1. Fork this repo.
2. Install from your fork: `/plugin install /path/to/your/fork`
3. Invoke in a throwaway directory: ask Claude to use the `agent-project-bootstrap` skill to set up a test project.
4. Verify the emitted files match your intended changes and all placeholders resolve correctly.

## What's in scope

- Template content and wording improvements
- New placeholders (with corresponding SKILL.md inventory updates)
- Emit process clarity (clearer steps, better verification instructions)
- Reference documentation (`references/design-decisions.md`, `references/obsidian-setup.md`)
- Persona files (`assets/vault/_meta/PERSONAS/`)
- Bug fixes and leak prevention
- Runtime adapters per ADR-001 (`adapters/<runtime>/HYDRATE.md` and supporting canonical files)
- Persona archetypes per ADR-001 (dev / autonomous-event / autonomous-cron / librarian, plus future archetypes the spec defines)
- ADR amendments (PRs against `docs/adr/`)

## What's out of scope

- Self-modifying or self-updating skill behaviour
- Non-Obsidian vault integrations (publish a separate skill for this)
- Changes to the release or sync workflow (those are vault-side decisions)

## License

This project is MIT licensed. By submitting a pull request, you agree that your contributions will be licensed under the same MIT license.
