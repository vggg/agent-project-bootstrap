# {{PROJECT_NAME}} wiki — reconciliation log

Append-only. Most recent entry at top. One entry per meaningful unit of work.

## [{{YYYY-MM-DD}}] genesis | {{PROJECT_NAME}} bootstrap

{{PROJECT_NAME}} bootstrapped via `agent-project-bootstrap@v0.3.1 mode:collab-repo-project`. Code repo: `{{CODE_REPO}}`. Collab repo: `{{COLLAB_REPO}}`. Personas scaffolded: see `BOOTSTRAP.md § The team`. Default Librarian runner: `@{{DEFAULT_RUNNER_HANDLE}}`; failover per `agents/librarian/FAILOVER.md`. First reconciliation entry seeded by the skill so the Librarian's `find -newer wiki/log.md` cycle has a timestamp baseline from day one.
