# Backlog — mechanisms (baron CLI, Phase 2+)

Deliberately deferred work with enough design recorded to pick up cold. Deferred
*candidates* (ideas without commitment) stay in `STATUS.md`; entries here are agreed
direction. See [ADR-003](adr/ADR-003-baron-cli.md) for the architecture these slot into.

## GitLab forge plugin (`baron-gitlab`)

**What:** a GitLab implementation of the forge Protocol, shipped as a *separate
distribution*, not in `baron` core. GitHub stays the only built-in.

**Design sketch:**

- Implements the same `Protocol` as `cli/src/baron/forge/base.py`
  (`name` / `available` / `default_branch` / `open_pr` / `list_open_prs`), backed by the
  `glab` CLI via subprocess — mirroring how `github.py` wraps `gh`. No GitLab SDK dep.
- Discovery via the Python entry-point group **`baron.forges`** (already wired: baron's own
  `get_forge()` resolves built-ins first, then scans the group). The plugin's
  `pyproject.toml` registers:

  ```toml
  [project.entry-points."baron.forges"]
  gitlab = "baron_gitlab:GitLabForge"
  ```

- Selection: an optional manifest key `forge: gitlab` (default `github`); forge-consuming
  commands pass it to `get_forge()`. The key is additive to `manifest.schema.md` and ignored
  by everything that doesn't consume forges.
- Unavailable tooling (`glab` not installed) raises the same `ForgeUnavailable` with an
  actionable message; non-forge commands are never affected.

**Why deferred:** no field forcing function yet — every real project to date is on GitHub
(single-account constraint, ADR-002 §1). Same rule as runtime adapters: add when a real
project on that forge exists.

## Worktree / branch-per-persona local topology (baron M6)

**What:** `baron` gains commands to *create and repair* the persona working-copy topology
(one shared object store via `git worktree`, one branch per persona), preventing the
stranding classes `baron status` currently only detects (ADR-003 §2.7). The M2 manifest
fields `workspace.clones` / `workspace.worktrees_root` are the forward-compatible seam.

## Forge-consuming commands (baron M4+)

**What:** the first commands that actually call `get_forge()` — e.g. `baron handoff`
PR-awareness (is a lock-holding PR still open?), the ADR-002 §3 lock-guard check as a baron
subcommand runnable in CI, and Merger precondition verification (ADR-002 §4: CI green +
SHA-bound REVIEW:PASS on the current head). Until then `forge/` is a Protocol + one stub.

## Consciously deferred inside M1–M3

- **`baron validate` does not resolve `manifest.personas[].spec` paths** to validate the
  referenced persona files in one pass — run validate over the directory instead.
- **`baron status` reads local git state only** (plus `--fetch`); it does not query the
  forge for open PRs / unmerged remote branches with no local ref.
- **`baron index` summarizes `_handoff/` only**; findings/decisions get numbering
  verification, not a regenerated table of contents (the index files are human-authored
  surfaces — see ADR-003 §2.2).
- **Handoff `updated:`-field maintenance** on close is not touched; only `status`/`closed:`
  are edited, textually.

- **`baron status` waivers (surfaced by first pilot triage, 2026-07-23):** a `.baron-waivers.yaml` (or manifest block) mapping check subjects to a waiver {reason, handoff-file, expires} so deliberately-parked items (e.g. a branch kept for a future experiment) downgrade red -> warn with the reason shown, instead of staying red forever. Expiry keeps waivers honest.
