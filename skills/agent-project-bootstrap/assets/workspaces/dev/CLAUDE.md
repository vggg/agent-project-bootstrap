# {{PROJECT_NAME}} — Claude Code Guide

> **Scope of this file:** engineering rules for the {{PROJECT_NAME}} codebase only.
> Session rituals, vault/Obsidian conventions, multi-agent handoffs, ADR triggers, and dev-log format live in
> `{{VAULT_PATH}}/projects/{{PROJECT_SLUG}}/COORDINATION.md`.
> Read that file at session start, every session.
>
> **Analyst agents:** this file is the dev guide. Your session instructions are at `{{WORKSPACE_BASE}}/[ProjectAnalyst]/CLAUDE.md`.

## Recent changes
<!-- 3 entries max, most recent first -->

## What this is

<!-- 2-3 sentences describing the product and its architecture. -->

## Stack

{{TECH_STACK}}

## Commands

```bash
# Fill in project-specific commands:
# dev server, production build, typecheck, lint, unit tests, E2E tests,
# DB migrate (dev), DB migrate (CI/prod), DB seed
```

## Project layout

```
# Fill in the source tree — top-level directories and their purpose
```

## Scope discipline — propose-before-doing

For any ticket that touches **more than 3 files**, introduces a **schema migration**, or changes a **public module boundary**: write the plan in chat and stop for {{USER_NAME}}'s review before writing code.

## Key architecture rules

### Auth & multi-tenancy
<!-- Describe auth pattern and tenancy constraints, e.g.:
- All data queries must filter by the active org/tenant ID
- Describe how the current user is fetched (helper function, middleware, etc.)
- Describe any impersonation or god-mode access pattern -->

### AI / external services
<!-- Describe how AI model IDs are referenced.
Convention: model IDs come from a single constants file — never hardcode model strings in feature code. -->

### Storage
<!-- Describe storage abstraction:
- Dev uses local filesystem; production uses cloud storage
- Never assume local storage in production — use the storage abstraction layer -->

### Error handling
<!-- Describe client-side error boundary pattern.
e.g. wrap major client components in an ErrorBoundary with a label. -->

## Testing requirements

Every code change — feature or bug fix — must ship with appropriate tests. No exceptions.

### Rule

| Change type | Required test |
|---|---|
| New feature (logic/utility) | Unit tests covering the happy path and key edge cases |
| New API route handler | At minimum a unit test for the handler logic; E2E test if user-facing |
| Bug fix | A regression test that **fails before the fix and passes after** |
| Schema migration | Confirm existing tests still pass; add tests if new query logic is introduced |
| Refactor | All existing tests must pass; add tests for any previously untested behaviour |

### What counts as "appropriate"

- Tests must assert observable behaviour, not implementation details
- A test that only checks "no error was thrown" is not sufficient — assert the actual output or side effect
- Mocking external services (AI APIs, cloud storage, email) is fine and expected; mocking the DB is not
- If a feature is purely cosmetic UI with no logic, note that explicitly in the PR — it is the only valid exemption

### Before opening a PR

Run and confirm passing:
```bash
# Add your typecheck, test, and build commands here
```

E2E tests run in CI. Run locally if the change touches a user-facing flow.

## Environment variables

```bash
# Copy .env.example → .env.local
# Required vars:
# (fill in from {{TECH_STACK}} — one line per key with a brief description)
```

## Shell commands for {{USER_NAME}}

When writing shell commands for {{USER_NAME}} to run:
- Always use `\` line continuation for multi-line commands so they can be copy-pasted directly.
- Never break a word or value across lines. A `\` must only appear at the end of a logically complete token.
- Exception: arguments whose values contain commas must stay on a single line entirely.
