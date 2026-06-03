# HYDRATE - Claude Code adapter (Tier 2)

> **Runtime:** Claude Code (home runtime).
> **What this does:** renders a runtime-neutral `agents/<slug>/persona.yaml` into the v0.3.x
> output shape Claude Code expects - a persona `CLAUDE.md` (persistent system-prompt context
> file) plus the `/vc` slash command. Goal: a project bootstrapped via the new canon is
> IDENTICAL to what v0.3.x produced by hand.
>
> **Tier:** 2 - persistent session context. Claude reads `CLAUDE.md` automatically each
> session, so the persona persists without re-injection (better than Tier 1). Capabilities
> are INSTRUCTED, not hard-enforced (Claude Tier-3 subagents deferred to v1.1, ADR section
> 10.5 / 10.8).
>
> **Read first:** `canon/PARTICIPATE.md` (capability ladder) and
> `canon/capability-vocab.v1.md` (verb contract).
>
> **Fallback:** if this adapter is absent, use `adapters/generic/HYDRATE.md`.

---

## Enforcement boundary

Claude Code (v1.0 scope) holds the persona in `CLAUDE.md` as instructions. There is no
tool allow-list applied at this tier, so **all** capabilities - whole-tool AND sub-tool - are
instruction-based. This is honest Tier 2: persistent + instructed, not enforced.

- `capabilities.allow` -> rendered as a "What you may do" section.
- `capabilities.deny` -> rendered as a "What never happens" section (the operative guardrail).
- Whole-tool enforcement (omitting tools) is a v1.1 upgrade via Claude subagents (deferred).

> Instruction-only guardrails still deliver real value (docs/LEARNINGS.md L3). The v0.3.x
> design was always Tier 2; we are faithfully reproducing it.

---

## Capability -> Claude rendering

Claude tool names are PascalCase (`Read`, `Write`, `Edit`, `Bash`). At Tier 2 these are not
allow-listed; they appear only in the "Tool hierarchy" prose for the agent's reference.

| Abstract verb (v1) | Rendered intent in CLAUDE.md |
|---|---|
| `read_code`, `read_collab` | "Read files in the code / collab repo" (Read/Grep) |
| `write_code` | "Create and modify code & tests" (Write/Edit) |
| `write_path: [..]` | "Write to these scopes only: <list>" |
| `open_pr` | "Open PRs via `gh`" |
| `run_tests` | "Run the test/coverage suite" |
| denied verbs | rendered into "What never happens" |

---

## Steps

### 1. Read the inputs
- `manifest.yaml` (repos, paths, backlog, owner).
- `agents/<slug>/persona.yaml` (the persona).
- Resolve workspace paths from `manifest.paths` (RELATIVE; never bake absolute home paths - F7).

### 2. Write the persona `CLAUDE.md`
Write to the persona's workspace as `CLAUDE.md` (Claude auto-loads it as session context).
Mirror the v0.3.x `__DEV__/AGENT.md` shape, with YAML frontmatter + these sections:

- **Frontmatter:** `persona`, `slug`, `archetype`, `status: active`, `created`.
- **Title + intro:** "You are <persona>, a <archetype> persona for <project>."
- **Identity table:** slug, git author, git email, commit prefix (`<slug>:`), routing label
  (`agent-<slug>`), plus the `git config` snippet.
- **Workspaces table:** each repo from `manifest.repos` with its relative path + access.
- **Scope:** `scope.summary` + `scope.focus` bullets.
- **Session-start ritual:** render `session_ritual` tokens (see table below).
- **Working rules:** branch `<slug>/<issue>-<slug>`, commit `<slug>: <type> | <desc>`, PR body.
- **What you may do:** from `capabilities.allow`.
- **What never happens:** from `capabilities.deny` (+ standard: force-push, git add -A).

### 3. Render the session ritual (v1 tokens, relative paths)
| Token | Rendered step |
|---|---|
| `sync_repos` | `git -C <repo.path> pull` for each repo with a remote (relative paths) |
| `read_conventions` | Read `<collab.path>/CONVENTIONS.md` + `COORDINATION.md` |
| `check_handoffs` | `grep -rl "^for: <Persona>\|^for: all" <collab.path>/_handoff/ \| xargs grep -l "^status: open"` |
| `check_backlog` | resolve `manifest.backlog`: file read, or `gh issue list --label agent-<slug>` |

### 4. Emit the `/vc` command
Write `.claude/commands/vc.md` mirroring the v0.3.x command: frontmatter
(`description`, `allowed-tools: Bash, Read`, `argument-hint`), the stage-thoughtfully rule
(never `git add -A`), the `<prefix> <operation> | <description>` convention, commit+push,
verify-the-push, and the hard rules (no force-push/amend/rebase on main; never commit `.env`).

### 5. Derive `AGENT.md` (optional, for collab repo)
The collab repo's `agents/<slug>/AGENT.md` is the human-readable manual, DERIVED from
`persona.yaml` (yaml canonical - F4). For Claude, the persona `CLAUDE.md` IS the operative
file; `AGENT.md` may mirror it for cross-runtime readability.

### 6. Verify (exit check)
- Persona `CLAUDE.md` exists with frontmatter + all sections.
- Identity (git author/email/prefix/label) matches `persona.yaml`.
- Every `deny` verb appears under "What never happens."
- `.claude/commands/vc.md` exists.
- Diff against a v0.3.x hand-authored example: structurally equivalent.

