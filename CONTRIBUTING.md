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

For PRs touching adapters, references, or the v1.0 canonical contract files, also run the bi-runtime acceptance test before pushing:

```bash
python tests/bi_runtime_accept.py
```

It validates that one `persona.yaml` hydrates to an equivalent behavior contract on both Claude Code and code-puppy adapters.

## Documentation is part of every PR

A PR that ships behavior, structure, or developer-experience changes without updating the relevant docs is not done. Same PR — not a follow-up.

Checklist (apply each line if relevant to the change):

- [ ] **Affected ADRs** — status frontmatter AND body headers reflect reality (no internal inconsistency between `status:` and the table header)
- [ ] **`CLAUDE.md`** — updated if conventions / layout / repo rules / canonicality changed
- [ ] **`README.md`** — updated if user-facing usage / modes / version / installation changed
- [ ] **`CHANGELOG.md`** — one line per PR minimum, under `[Unreleased]` between releases
- [ ] **`STATUS.md`** — mark multi-step plan progress (e.g. ADR-001 §10 step N done)

Reviewers must request docs before merging, not after.

**Exception:** strictly cosmetic single-file changes (typo fixes, broken link updates, status syncs) may skip the broader checklist — but still update `CHANGELOG.md` under `[Unreleased]`.

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
