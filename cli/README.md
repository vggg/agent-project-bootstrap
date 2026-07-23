# baron — the collab-repo CLI (Phase 2: conventions → mechanisms)

`baron` turns the multi-agent coordination *conventions* that
`agent-project-bootstrap` emits into *mechanisms*: a small CLI that validates the
canonical specs, reports clone/branch/ledger divergence, and performs the
race-prone record-keeping operations (finding/decision numbering, handoff
lifecycle) safely.

**Design principle (ADR-003, `../docs/adr/ADR-003-baron-cli.md`): the
markdown/git substrate IS the database.** baron is a disciplined reader/writer
over the same human-legible collab-repo files the personas use
(`manifest.yaml`, `persona.yaml`, `findings/index.md`, `decisions/index.md`,
`_handoff/*.md`, `wiki/status.md`). It never introduces another store, and every
file it writes remains fully human/agent-legible.

Dependencies: **typer + pyyaml only**. `git` is driven via subprocess. `gh` is an
accepted prerequisite for forge features only — everything below (M1–M3) works
without `gh` installed.

## Install

```bash
# from the repo root, with uv:
uv tool install ./cli            # installs the `baron` console script
# or for development:
uv run --project cli baron --help
# or with plain pip (>= 3.10):
pip install ./cli
```

## Commands

### `baron validate [PATH]` (M1)

Validate `persona.yaml` / `manifest.yaml` — a single file, or every one
discovered under `PATH`. Schemas are declarative Python data
(`src/baron/schemas.py`) formalized from the prose specs in
`../skills/agent-project-bootstrap/references/`; the FROZEN 10-verb capability
vocabulary is embedded and drift-guarded by a test that re-parses
`capability-vocab.v1.md`.

Checks: YAML parse, missing/unknown fields, types, verbs outside the vocabulary,
allow/deny overlap (including `write_path` scope overlap), unfilled
`{{PLACEHOLDER}}` tokens.

**Template rule:** directory discovery skips files whose path contains a
template marker directory (`assets/collab-repo/` or `legacy/`) — emit-time
templates legitimately carry placeholders and often aren't valid YAML at all.
Fixture paths (`tests/examples/`) are validated but exempt from the placeholder
check only. An explicitly named file is always validated.

Exit 0 = no errors (warnings allowed) / 1 = errors. `--json` for machines.

```bash
baron validate tests/examples/tess/persona.yaml
baron validate . --json
```

### `baron status [--fetch] [--sla N] [--json]` (M2)

Run from a collab repo (or `--collab PATH`). Reads `manifest.yaml` — including
the optional `workspace.clones` / `workspace.worktrees_root` fields (see
`../skills/agent-project-bootstrap/references/manifest.schema.md`) — and
reports, with severity:

| Check | Severity | Meaning |
|---|---|---|
| `ahead` | red | commits never pushed to origin (stranded work) |
| `behind` | red | origin commits never pulled (stale canonical clone) |
| `unmerged-branch` | red | local branch not merged to origin default, with last-commit age |
| `handoff-overdue` | red | `status: open` handoff older than the SLA (default 14 days) |
| `dirty` | warn | uncommitted paths |
| `ledger-stale` | warn | newest F/D entry date older than the newest `docs/`/`src/` commit in the code repo (**heuristic**, labeled as such) |
| `wiki-stale` | warn | `wiki/status.md` `updated:` older than the newest finding entry |

Use `--fetch` to refresh each working copy's origin refs first — without it,
remote-side divergence (the `behind` class) is invisible. Exit 0 = green
(warnings allowed) / 1 = any red (CI-usable).

### `baron finding new` / `baron decision new` (M3)

```bash
baron finding new --title "Tracker-gated recall" --author carson
baron decision new --title "Adopt fps-aware segmentation" --author terrence --body-file body.md
```

Parses the index for the max ID (both `### F<N>` headings and `| F<N> |` table
rows), allocates the next, appends a house-style entry
(`### F<N> — <title> (<date>, <author>)`), commits, and pushes. **On push
rejection** (someone else claimed the number first): roll back, `pull --rebase`,
re-parse, renumber, retry — bounded (`--retries`, default 3). git's push
atomicity is the lock; there is no other store. `--no-push` for offline work.
Dates come from a single injectable clock (`src/baron/clock.py`).

### `baron handoff create|close|list` (M3)

```bash
baron handoff create --for tess --from rex --title "Review the seam" --priority high
baron handoff close _handoff/2026-07-22-review-the-seam.md --note "Done, see F9."
baron handoff list --open
```

`create` writes `_handoff/YYYY-MM-DD-<slug>.md` with the standard frontmatter
(`created` / `status: open` / `for` / `from` / `priority`). `close` flips
`status` to `done`, adds a `closed:` date and an optional blockquote note, then
`git mv`s the file to `_handoff/archive/YYYY/` — **archive, never delete**, with
history preserved. Status edits are textual so prose is never reflowed.

### `baron index` (M3)

Regenerates a marker-delimited summary block (`BEGIN/END BARON INDEX` HTML
comments) in `_handoff/README.md` (creating it if absent): open/done/archived
counts plus a table of open handoffs (file, for, from, age). Also verifies
finding/decision numbering: duplicates are errors (exit 1); gaps and
out-of-order headings are **report-only** warnings — baron never renumbers
history.

## Forges

`src/baron/forge/` holds a small `Protocol` (`base.py`) with one built-in
implementation, GitHub via `gh` subprocess (`github.py`). Other forges are
plugins discovered through the `baron.forges` entry-point group; GitLab is
backlog — design sketch in `../docs/BACKLOG.md`.

## Development

```bash
uv run --project cli pytest cli/tests    # from the repo root
```

The suite includes the capability-vocabulary drift guard, a synthetic divergent
git topology reproducing the 2026-07-22 triple-stranding incident classes, and
the ledger push-rejection race test.
