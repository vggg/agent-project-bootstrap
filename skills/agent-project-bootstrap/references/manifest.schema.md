# `manifest.yaml` Schema v1

> The CANONICAL, runtime-neutral PROJECT spec: what repos exist, where the backlog lives, and
> which personas are on the team. Consumed by the orchestrator (ORCHESTRATE.md) at bootstrap
> and by adapters when hydrating personas. Runtime-neutral; names no runtime tools.
>
> This schema is where the Phase 2 "location & transport independence" theme (F1/F7/F8) is
> resolved structurally.

## Fields

| Field | Req | Type | Notes |
|---|---|---|---|
| `project.name` | yes | str | e.g. `tasklib-agents` |
| `project.description` | yes | str | one line |
| `repos` | yes | list | each repo the team operates on (see below) |
| `paths.strategy` | yes | enum | `relative` (default, REQUIRED for portability) or `absolute` |
| `paths.root` | no | str | anchor for relative resolution; default = collab repo root |
| `backlog.source` | yes | enum | `file` or `github_issues` or `jira` (resolves F8) |
| `backlog.location` | yes | str | path (for `file`) or repo/project ref (for trackers) |
| `personas` | yes | list | roster: each entry points at a `persona.yaml` |

### repos[]

| Field | Req | Notes |
|---|---|---|
| `id` | yes | logical name used by capability verbs: `code`, `collab` |
| `path` | yes | location RELATIVE to `paths.root` (F7 fix - never absolute) |
| `remote` | no | optional git remote; absent means local-only (valid, per Phase 2) |
| `role` | yes | `code` (app) or `collab` (coordination substrate) |

### personas[]

| Field | Req | Notes |
|---|---|---|
| `slug` | yes | matches a `persona.yaml` slug |
| `spec` | yes | path to the persona.yaml (relative) |

## Example (tasklib-agents, derived from the Phase 2 dogfood)

```yaml
project:
  name: tasklib-agents
  description: Autonomous multi-agents to improve testing coverage for tasklib.
paths:
  strategy: relative          # F7: hydration emits ../code, never /Users/...
  root: .                     # resolved from the collab repo root
repos:
  - id: code
    path: ../code             # relative - travels on re-clone
    role: code
    # remote: omitted -> local-only (Phase 2 proved this is valid)
  - id: collab
    path: .
    role: collab
backlog:
  source: file                # F8: not hardcoded to GitHub
  location: backlog.md        # lives in the collab repo
personas:
  - slug: tess
    spec: agents/tess/persona.yaml
```

## How this fixes the Phase 2 friction

- **F7 (absolute paths):** `paths.strategy: relative` + relative `repos[].path` means the
  adapter renders `git -C ../code ...`, never a home-dir absolute path. Re-clone anywhere and
  it still works.
- **F8 (GitHub-only backlog):** `backlog.source`/`location` make the `check_backlog` ritual
  token resolve to a file read OR an issue-tracker query, per project.
- **F1 (cwd coupling):** ORCHESTRATE.md + the adapter document that the runtime session starts
  at `paths.root`; discovery and relative paths resolve from there.

## Changelog

- **v1** (Phase 3): new, derived from the Phase 2 dogfood. Encodes location & transport
  independence (relative paths, configurable backlog source) to fix F1/F7/F8.
