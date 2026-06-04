# HYDRATE - Claude Code adapter (Tier 2 + Tier 3)

> **Runtime:** Claude Code (home runtime).
> **What this does:** renders a runtime-neutral `agents/<slug>/persona.yaml` into the
> highest-fidelity shape this Claude session supports:
> - **Tier 3** — a native Claude **subagent** at `.claude/agents/<slug>.md` with an
>   **enforced** tool allow-list (whole-tool denials become real). Analogous to the
>   code-puppy adapter's JSON sub-agent.
> - **Tier 2** — a persona `CLAUDE.md` (persistent session context); capabilities are
>   **instructed**, not enforced. This is the v0.3.x output shape — a project hydrated at
>   Tier 2 is IDENTICAL to what v0.3.x produced by hand.
>
> **Read first:** `canon/PARTICIPATE.md` (capability ladder) and
> `canon/capability-vocab.v1.md` (verb contract + enforceability classes).
>
> **Fallback:** if this adapter is absent, use `adapters/generic/HYDRATE.md` (Tier 1).

---

## Which tier? (resolution)

Tier comes from config, defaulting to `auto`. The config keys live in a **namespaced
adapter block** so the canonical schemas stay runtime-neutral — each adapter owns its own
keys under `adapters.<runtime>`:

| Source | Key | Values |
|---|---|---|
| Project default (`manifest.yaml`) | `adapters.claude.tier` | `auto` \| `2` \| `3` (default `auto`) |
| Per-persona override (`persona.yaml`) | `runtime.adapters.claude.tier` | `auto` \| `2` \| `3` |

**Precedence:** persona override > project default > `auto`.

**`auto` self-assessment** — you, the hydrating agent, decide in-context. Render **Tier 3**
only if ALL of these hold; otherwise render **Tier 2**:

1. You can create AND read back a file under `<code_repo>/.claude/agents/` (write access there).
2. This session actually exposes Claude's subagent mechanism — i.e. subagents are usable
   here, not a constrained sub-session / CI shell that can't host them.
3. There is no explicit `claude.tier: 2` override (project or persona).

> An explicit `tier: 2` or `tier: 3` always wins over `auto`. If `tier: 3` is set but this
> session can't host subagents (checks 1–2 fail), do NOT emit a dead subagent file: fall back
> to Tier 2 and report the downgrade with one line of reasoning. Graceful degradation is the
> rule (PARTICIPATE.md) — Tier 2 always works; Tier 3 is the upgrade where supported.

---

## Enforcement boundary

| Capability class | Tier 2 (`CLAUDE.md`) | Tier 3 (subagent) |
|---|---|---|
| **Whole-tool** (e.g. deny all writes / all shell) | instructed | **ENFORCED** via the `tools:` allow-list — omit the tool and the action is impossible |
| **Sub-tool** (e.g. allow `open_pr`, deny `merge_pr` — both via `Bash`) | instructed | instructed (the parent tool is granted; denial is prose only) |

Tier 3 closes the gap the v1.0 Claude adapter left open (ADR §10.5 / §10.8): whole-tool
denials become real, matching the contract the code-puppy adapter delivers. Sub-tool denials
remain instruction-only at BOTH tiers — **do not oversell them** (see
`canon/capability-vocab.v1.md` enforceability classes; `docs/LEARNINGS.md` L3: instruction-only
guardrails still add real value, but say honestly what is enforced vs. instructed).

---

## Capability → Claude tool mapping (Tier 3 enforced layer)

Claude tool names are PascalCase. Build the **minimal** `tools` allow-list — include a tool
only if at least one allowed verb needs it.

| Abstract verb (v1) | Adds to `tools` |
|---|---|
| `read_code`, `read_collab` | `Read`, `Grep`, `Glob` |
| `write_code` | `Write`, `Edit` |
| `write_path: [..]` | `Write`, `Edit` (allowed path scopes → instructions in the body) |
| `open_pr`, `run_tests` | `Bash` |

**Whole-tool denials:** if NO allowed verb needs a tool, it MUST be absent — the runtime
hard-denies it. A read-only persona (e.g. a reviewer/librarian with no
`write_*`/`open_pr`/`run_tests` verbs) gets `tools: Read, Grep, Glob` — `Write`/`Edit`/`Bash`
are absent and genuinely unavailable.

**Sub-tool denials** (`merge_pr`, `push_main`, `force_push`, denied `write_path` scopes,
`edit_other_personas`): the parent tool (`Bash` / `Write`) is needed for allowed ops, so
render these into the body's "What never happens" block.

> At **Tier 2** none of this is allow-listed; the same verbs render only as prose (the
> "What you may do" / "What never happens" sections of the persona `CLAUDE.md`).

---

## Steps

### 1. Read the inputs
- `manifest.yaml` (repos, paths, backlog, owner, `adapters.claude.tier`).
- `agents/<slug>/persona.yaml` (the persona; `runtime.adapters.claude.tier` override if set).
- Resolve workspace paths from `manifest.paths` (RELATIVE; never bake absolute home paths — F7).

### 2. Resolve the tier
Apply precedence (persona override > project default > `auto`) and run the `auto`
self-assessment if unresolved. Record the chosen tier + a one-line reason.

### 3a. Tier 3 — write the Claude subagent
Write to `<code_repo>/.claude/agents/<slug>.md` (project-scoped → travels with the repo;
already present on re-clone, so failover = re-clone, no re-hydration unless `persona.yaml`
changed). Schema: YAML frontmatter (`name`, `description`, `tools`) + the system-prompt body.

```markdown
---
name: <slug>
description: <Persona> — <archetype> for <project>. Use when work is routed to the <slug> persona (label agent-<slug>) or the user asks <Persona> to act.
tools: <minimal allow-list from the mapping above, comma-separated>
# model: <persona runtime.model_hint, if set; else omit to inherit the session default>
---
You are <Persona>, the <archetype> persona for <project>.

<scope.summary>

## Identity
- Git author: <git_name> / <git_email>
- Commit prefix: <commit_prefix>
- Routing label: <routing_label>
Before committing, set per-repo git config:
  git config user.name "<git_name>"
  git config user.email "<git_email>"

## Scope
- <scope.focus[0]>
- <scope.focus[1]>
- ...

## Session-start ritual (every session, in order)
<render session_ritual — see step 4>

## What you may do
<one line per capabilities.allow verb, human-phrased>

## What never happens (sub-tool guardrails — self-enforced; the `tools:` allow-list already hard-blocks the rest)
<one imperative line per capabilities.deny verb>
- Never git add -A / git add . (stage only intended files; avoids leaking secrets).

## Commit workflow
Use the `/vc` command to stage, commit (prefix "<commit_prefix>"), and push per the project's
conventions. `_handoff/` files may be direct-pushed; substantive changes go via PR.
```

The `tools:` line is the **enforced** layer; the "What never happens" block is the
**instructed** layer for sub-tool denials. (Mirror of the code-puppy two-layer contract.)

### 3b. Tier 2 — write the persona `CLAUDE.md`
Write to the persona's workspace as `CLAUDE.md` (Claude auto-loads it as session context).
Mirror the v0.3.x `__DEV__/AGENT.md` shape, with YAML frontmatter + these sections:

- **Frontmatter:** `persona`, `slug`, `archetype`, `status: active`, `created`.
- **Title + intro:** "You are <persona>, a <archetype> persona for <project>."
- **Identity table:** slug, git author, git email, commit prefix (`<slug>:`), routing label
  (`agent-<slug>`), plus the `git config` snippet.
- **Workspaces table:** each repo from `manifest.repos` with its relative path + access.
- **Scope:** `scope.summary` + `scope.focus` bullets.
- **Session-start ritual:** render `session_ritual` tokens (step 4).
- **Working rules:** branch `<slug>/<issue>-<slug>`, commit `<slug>: <type> | <desc>`, PR body.
- **What you may do:** from `capabilities.allow`.
- **What never happens:** from `capabilities.deny` (+ standard: force-push, git add -A).

All capabilities here are INSTRUCTED — no tool allow-list is applied at this tier.

### 4. Render the session ritual (v1 tokens, relative paths)
Used by both tiers (in the subagent body at Tier 3, in `CLAUDE.md` at Tier 2).

| Token | Rendered step |
|---|---|
| `sync_repos` | `git -C <repo.path> pull` for each repo with a remote (relative paths) |
| `read_conventions` | Read `<collab.path>/CONVENTIONS.md` + `COORDINATION.md` |
| `check_handoffs` | `grep -rl "^for: <Persona>\|^for: all" <collab.path>/_handoff/ \| xargs grep -l "^status: open"` |
| `check_backlog` | resolve `manifest.backlog`: file read, or `gh issue list --label agent-<slug>` |

### 5. Emit the `/vc` command
Write `.claude/commands/vc.md` mirroring the v0.3.x command: frontmatter
(`description`, `allowed-tools: Bash, Read`, `argument-hint`), the stage-thoughtfully rule
(never `git add -A`), the `<prefix> <operation> | <description>` convention, commit+push,
verify-the-push, and the hard rules (no force-push/amend/rebase on main; never commit `.env`).
The same command serves both tiers; the Tier-3 subagent body points at it.

### 6. Derive `AGENT.md` (optional, for collab repo)
The collab repo's `agents/<slug>/AGENT.md` is the human-readable manual, DERIVED from
`persona.yaml` (yaml canonical — F4). For Claude, the operative file is the subagent
(Tier 3) or the persona `CLAUDE.md` (Tier 2); `AGENT.md` may mirror it for cross-runtime
readability.

### 7. Verify (exit check)

**Both tiers:**
- Identity (git author/email/prefix/label) matches `persona.yaml`.
- Every `deny` verb appears under "What never happens."
- `.claude/commands/vc.md` exists.

**Tier 3:**
- `.claude/agents/<slug>.md` exists with frontmatter (`name`, `description`, `tools`) + body.
- `tools` is MINIMAL: every listed tool is required by an allowed verb; no extras.
- Whole-tool denials honored: the tool for any denied whole-tool capability is ABSENT.
- (Optional, the real proof) the subagent is discoverable/invocable in this session; ask it to
  recite its identity + guardrails.

**Tier 2:**
- Persona `CLAUDE.md` exists with frontmatter + all sections.
- Diff against a v0.3.x hand-authored example: structurally equivalent.
