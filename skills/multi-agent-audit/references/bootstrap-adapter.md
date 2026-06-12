# Adapter — agent-project-bootstrap v1.x layout

Load this reference when Step 0 detects the agent-project-bootstrap collab-repo-project layout (presence of `manifest.yaml` + `agents/<name>/persona.yaml` + `adapters/<runtime>/`).

This adapter tells the audit **exactly where to mine each metric** in a project that follows the bootstrap convention, so Step 1 doesn't need heuristics.

## Layout signature

A bootstrap v1.x project has:

```
<collab-repo>/
  manifest.yaml                      # roster + project config
  CONVENTIONS.md                     # vault-wide rules
  COORDINATION.md                    # multi-agent protocol
  CLAUDE.md                          # entry pointer
  START.md / ORCHESTRATE.md / PARTICIPATE.md   # neutral entrypoints (v1.x)
  agents/
    <persona>/
      persona.yaml                   # machine-readable persona (v1.x)
      AGENT.md                       # human-readable persona (v0.x + v1.x)
      FAILOVER.md                    # cron persona's failover runbook
  adapters/
    claude/HYDRATE.md
    code-puppy/HYDRATE.md
    generic/HYDRATE.md
  _handoff/                          # async cross-agent messages
  decisions/                         # decision notes + ADR pointers
  findings/                          # investigations, dev logs, UAT
  wiki/                              # librarian-synthesized knowledge layer
```

Detect:

```bash
test -f <collab-repo>/manifest.yaml && \
test -d <collab-repo>/agents && \
test -d <collab-repo>/_handoff && \
echo "agent-project-bootstrap v1.x detected"
```

If `adapters/` is also present, it's confirmed v1.x. If `agents/<name>/persona.yaml` files exist, definitely v1.x. v0.x is the same layout without `adapters/` or `persona.yaml` (only `AGENT.md`).

## Roster mining

### Declared roster

Authoritative source: `manifest.yaml` `agents:` block. Schema:

```yaml
agents:
  - slug: dave
    archetype: dev
    runtime: interactive
    git_email: dave@example.com
    routing_label: agent-dave
    write_areas: [src/, tests/]
  - slug: librarian
    archetype: librarian
    runtime: cloud-routine     # autonomous via /schedule
    trigger: cron
    schedule: "0 15 * * *"
```

Parse `agents:` block; each entry maps to one declared actor. Capture: `slug`, `archetype`, `runtime`, `trigger`, declared `write_areas`.

Per-persona detail: `agents/<slug>/persona.yaml` — has `capabilities.allow:` / `capabilities.deny:` lists (the canonical guardrails) and per-persona overrides.

### Observed actors

Standard `git log` + `gh pr/issue/review` queries from `references/platform-integrations.md`. The bootstrap-specific signal:

**Commit prefix attribution.** Personas commit with a prefix matching their slug:

```bash
git -C <code-repo> log --since="<W>" --format='%H|%s|%an|%ae' \
  | awk -F'|' '$2 ~ /^(iris|dave|kris|vera|ivy):/ {
      split($2, parts, ":"); print $1"|"parts[1]
    }'
```

This resolves the identity-collision case where the same human-account commits as different personas — the prefix is authoritative over the email.

## Coordination substrate

Handoffs live in `_handoff/` as markdown files with YAML frontmatter:

```yaml
---
created: 2026-06-10
status: open
for: Vera
from: Iris
priority: high
project: GardenTwin
---
```

### Mining queries

```bash
# Count handoffs in window
ls -1 <collab-repo>/_handoff/*.md | \
  xargs -I{} grep -l "^created: 2026-06" {} | wc -l

# Open vs done split
grep -l "^status: open" <collab-repo>/_handoff/*.md | wc -l
grep -l "^status: done" <collab-repo>/_handoff/*.md | wc -l

# Open handoff age
grep -l "^status: open" <collab-repo>/_handoff/*.md \
  | xargs grep -H "^created:" \
  | awk -F'created: ' '{print $2}'
```

### Handoff edges (network analysis)

For each `_handoff/` file, extract `from:` and `for:` to build the handoff edge list (see `references/advanced-metrics.md § Network analysis`). Note that the bootstrap convention uses `for: all` or `for: iris` as broadcast — handle these as edges from `<from>` to each canonical actor (for `for: all`) or to the named recipient.

## Decisions and findings

```
<collab-repo>/decisions/    # full ADRs or pointer stubs
<collab-repo>/findings/     # investigations, dev logs, UAT outputs
<collab-repo>/wiki/         # librarian's synthesized knowledge
```

The bootstrap convention: ADRs live in the **code repo** (`docs/adr/ADR-NNN-slug.md`) once accepted, with a pointer stub in `<collab-repo>/decisions/`. Mine both:

```bash
# Pointer stubs
ls <collab-repo>/decisions/*.md | wc -l

# Actual ADRs
ls <code-repo>/docs/adr/ADR-*.md 2>/dev/null | wc -l
```

For the Knowledge-capture axis, sample:

- How many findings have `status: tracked` (vs `status: open`)? Tracked = converted to a GitHub issue. Conversion rate is a coordination signal.
- How current is the wiki log (`<collab-repo>/wiki/log.md`)? Last entry timestamp vs end of window.

## Guardrail mining

### Declared guardrails

| Source | What to extract |
|---|---|
| `CONVENTIONS.md` § *Vault commits* / *What never happens* | force-push, `add -A`, push-to-main, amend/rebase rules |
| `COORDINATION.md` § *Multi-agent dev rules* / *Hot files* | claim-before-coding, schema migration discipline, hot-file serialization |
| `agents/<slug>/persona.yaml` `capabilities.deny:` | per-persona denies (capability-level) |
| `adapters/<runtime>/HYDRATE.md` | runtime-mapped allow-lists |

### Enforced vs instructed (the load-bearing question)

For each declared deny in `persona.yaml`, check whether the runtime adapter actually omits the corresponding tool:

| Declared deny | Enforced if... |
|---|---|
| `merge_pr` | Adapter's tool list omits the merge mechanism (e.g., Claude subagent doesn't grant write access to GitHub merge API) |
| `force_push` | Branch protection on main exists with `allow_force_pushes: false` |
| `write_wiki` | Persona's subagent (Tier-3) gets a tool list excluding writes outside its declared write_areas |
| `push_main` | Branch protection requires PR + reviews (any commit on main goes through PR) |

Cross-reference with `gh api repos/<o>/<r>/branches/main/protection`. If the protection rule for the declared deny is missing, the deny is **instructed-only** — surface in drift.

This is the v1.0 honesty boundary documented in `LEARNINGS.md L3`: instructed-only denies still add value, but they must be classified honestly.

## Backlog mining

GitHub issues are the standard backlog. Bootstrap adds the `agent-<slug>` label convention:

```bash
# Tickets claimed by each persona
gh -R <owner>/<repo> issue list --state open --label "agent-<slug>" --json number,title

# Unclaimed available work
gh -R <owner>/<repo> issue list --state open --no-assignee --json number,title
```

For the bootstrap collab-repo-project pattern, ADR-relevant changes get labelled in the PR; cross-reference for the decision-filing-rate metric.

## Ritual mining

Bootstrap convention prescribes:

- **Session-start checklist** in `COORDINATION.md` — pull vault → read CONVENTIONS → read project context → check handoffs → check backlog. Check ritual adherence by sampling a handoff or dev-log around session-start times.
- **Dev-log per session** in `findings/dev-log/YYYY-MM-DD.md`. Count files vs active dev-days from `git log` for the dev persona.
- **EOD logs** for non-dev personas (e.g., `ClaudeDesigner/YYYY-MM-DD-eod.md`).

Compute `dev_log_adherence` and `eod_log_adherence` per persona.

## Non-committing agent reminder

The bootstrap pattern explicitly supports non-committing agents:

- **Librarian (cron)** — writes to vault `wiki/` directory. May commit (if vault is git-tracked) or may not (if vault is fully external). If `wiki/` is in the collab repo, the librarian's writes appear in `git log`. If the wiki is in a separate vault, the librarian's work is invisible to `git log` of the audited repos — surface as non-committing in the inventory.
- **PR reviewer (gh-actions-event)** — runs in CI; bot account; appears in `gh api .../pulls/<n>/reviews` but never commits to feature branches.

For agent-project-bootstrap audits: **always** check for non-committing review bots and cron librarians in the inventory (Step 0.5). Missing them inflates the autonomy split.

## Headline metric mapping

The intervention tax for bootstrap projects:

- **Autonomous initiated tasks** = PRs/handoffs originated by `runtime: cloud-routine | gh-actions-cron | gh-actions-event` personas + bot accounts.
- **Hybrid initiated tasks** = PRs/handoffs originated by `runtime: interactive` personas (Dave, Kris, Vera, Ivy). Count separately; for the headline, hybrid sits between human and autonomous but should NOT be collapsed with autonomous when computing intervention tax (since hybrid agents are human-initiated even if they decide internally).
- **Human intervention events** = Vikram's PR comments, corrections, redos, fix-up commits against autonomous- or hybrid-initiated PRs.

For audits of this project family, report intervention tax broken down by *autonomous vs hybrid* — both signals matter.

## Output location for bootstrap audits

Per `SKILL.md § Output location convention`:

- Default: `<collab-repo>/audit/<project>-audit-<YYYY-MM-DD>.{md,html}` and `<collab-repo>/audit/snapshots/<timestamp>.json`.
- The skill **writes** these files; **does not** commit them. The human owner runs the collab repo's standard commit workflow (the `/vc` skill in vault-hosted collab repos; manual `git add` + `git commit` elsewhere).

The `audit/` folder may not exist on first run — create it; that's not "modifying the audited repo" (it's the auditor's output area).
