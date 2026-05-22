# Contributing

## Scope

Refinements to the existing pattern are welcome. If you want to explore a fundamentally different direction — different agent archetypes, non-Obsidian vault integrations, orchestrator-based patterns — fork this and publish a separate skill rather than expanding this one's scope.

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

## What's out of scope

- New agent archetypes beyond Iris / Dev-1 / Dev-2 / Analyst / Designer
- Self-modifying or self-updating skill behaviour
- Non-Obsidian vault integrations (publish a separate skill for this)
- Changes to the release or sync workflow (those are vault-side decisions)

## License

This project is MIT licensed. By submitting a pull request, you agree that your contributions will be licensed under the same MIT license.
