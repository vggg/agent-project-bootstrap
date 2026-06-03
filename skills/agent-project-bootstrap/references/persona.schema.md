# `persona.yaml` Schema v1

> The CANONICAL, runtime-neutral definition of one persona. `agents/<persona>/AGENT.md` is
> DERIVED from this (yaml canonical, md generated — resolves F4 drift). Adapters consume this
> file unchanged; nothing here names a runtime tool.
>
> Provenance: every field below was used by the Phase 1–2 dev persona (Tess). No speculative
> fields (YAGNI).

## Fields

| Field | Req | Type | Notes |
|---|---|---|---|
| `persona` | yes | str | Display name, e.g. `Tess` |
| `slug` | yes | str | kebab/lower id, e.g. `tess` (agent name + label stem) |
| `archetype` | yes | enum | `dev` (v1). Future: `librarian`, `reviewer`, `autonomous-*` |
| `identity.git_name` | yes | str | git author name |
| `identity.git_email` | yes | str | git author email (may use `{{IDENTITY_DOMAIN}}`) |
| `identity.commit_prefix` | yes | str | e.g. `tess:` |
| `identity.routing_label` | yes | str | e.g. `agent-tess` |
| `capabilities.allow` | yes | list | v1 verbs (see capability-vocab.v1.md); `write_path` is parametric |
| `capabilities.deny` | yes | list | v1 verbs; sub-tool denials become persona-body instructions |
| `scope.summary` | yes | str | one-paragraph mission |
| `scope.focus` | yes | list[str] | bullet responsibilities |
| `session_ritual` | yes | list | ordered intent tokens (see below) |
| `runtime.trigger` | no | enum | `interactive` (default) \| `event` \| `cron` |
| `runtime.model_hint` | no | str | optional model pin; adapter may apply (code-puppy does) |

## Session-ritual tokens (intent-level — resolves F8 transport coupling)

| Token | Intent |
|---|---|
| `sync_repos` | bring all configured repos up to date |
| `read_conventions` | read the collab repo's CONVENTIONS + COORDINATION |
| `check_handoffs` | find open handoffs addressed to this persona or `all` |
| `check_backlog` | read the project backlog (source per manifest: file or issue-tracker) |

> v0 used `pull_both_repos` (transport-coupled). v1 renames to `sync_repos` (intent only).
> The adapter + manifest decide HOW to sync and WHERE the backlog lives.

## Example (Tess, v1)

```yaml
persona: Tess
slug: tess
archetype: dev
identity:
  git_name: Tess
  git_email: tess@{{IDENTITY_DOMAIN}}
  commit_prefix: "tess:"
  routing_label: agent-tess
capabilities:
  allow:
    - read_code
    - read_collab
    - write_code
    - write_path: [findings, _handoff]
    - open_pr
    - run_tests
  deny:
    - write_path: [wiki]
    - merge_pr
    - push_main
    - force_push
    - edit_other_personas
scope:
  summary: >-
    Raise and maintain automated test coverage. Find under-tested modules,
    write fast/isolated tests, report coverage deltas.
  focus:
    - Increase line/branch coverage on assigned modules
    - Write unit + integration tests; keep them fast and isolated
    - Report coverage deltas in findings/ after each session
session_ritual:
  - sync_repos
  - read_conventions
  - check_handoffs
  - check_backlog
runtime:
  trigger: interactive
```

## Derivation rule (F4)

`persona.yaml` is the single source of truth. `agents/<persona>/AGENT.md` is GENERATED from
it (identity, scope, ritual, allow/deny rendered to prose). Never hand-edit AGENT.md; edit
the yaml and re-derive. Adapters likewise read the yaml, not the md.

## Changelog

- **v1** (Phase 3): finalized from the Phase 1 lean draft. Renamed `pull_both_repos` ->
  `sync_repos`. Adopted parametric `write_path`. Added optional `runtime.model_hint`.