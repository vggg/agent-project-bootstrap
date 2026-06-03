# HYDRATE - generic adapter (Tier 1, always-works fallback)

> **Runtime:** ANY. The mandatory floor of the capability ladder (ADR section 10.4). If a
> runtime has no native sub-agents (Tier 3) and no persistent session/context file (Tier 2),
> it uses THIS. Every runtime can run it, because it needs nothing but "follow instructions
> each turn."
>
> **Tier:** 1 - in-prompt, fully instruction-based. NOTHING is hard-enforced; the operating
> agent self-enforces by re-reading the spec. That is the design, not a weakness - see
> docs/LEARNINGS.md L3 (instruction-only guardrails demonstrably catch real mistakes).
>
> **Read first:** `canon/PARTICIPATE.md` (capability ladder) and
> `canon/capability-vocab.v1.md` (verb contract).

---

## When you (the operating agent) are here

You cannot register a scoped sub-agent and have no persistent system-prompt file that
survives between turns. So you cannot "install" a persona once and trust the runtime to keep
it. Instead you **carry the persona yourself, every turn.**

The core loop:

> **Each turn: (1) re-read `persona.yaml`, (2) check the action you are about to take against
> `capabilities.allow` / `deny`, (3) act only if allowed, (4) follow the ritual + conventions.**

There is no hydration ARTIFACT to emit (no JSON agent, no CLAUDE.md). "Hydration" here means
loading the spec into your working context and committing to honor it.

---

## Steps

### 1. Load the project + persona spec
- Read `manifest.yaml` -> find your persona `spec` path and the `repos` / `backlog` / `paths`.
- Read your `agents/<slug>/persona.yaml`.
- Read `CONVENTIONS.md` + `COORDINATION.md`.
- Keep `persona.yaml` close - re-open it whenever context may have drifted (after long tool
  output, after a summary, at the start of each new sub-task).

### 2. Build your self-enforcement checklist (from `capabilities`)
Translate the verbs into a literal yes/no list you consult before EVERY action:

- `capabilities.allow` -> "I MAY ..." (e.g. read_code, write_code, run_tests).
- `capabilities.deny`  -> "I MUST NOT ..." (e.g. merge_pr, push_main, force_push,
  edit_other_personas, and any denied write scope such as wiki).

Before any file write, shell command, or git action, ask: does the verb behind this action
appear under allow? Is it under deny? If denied or not in allow, **do not do it** - drop a
`_handoff/` to the owner instead (the golden rule from PARTICIPATE.md).

> Tier-1 reality: the runtime WILL hand you the tools to violate these (there is no allow-list
> to remove them). The guardrail is your discipline. Treat `deny` as inviolable.

### 3. Set git identity (every session, before committing)
Use `identity.git_name` / `identity.git_email`, and prefix commits with
`identity.commit_prefix`. Never `git add -A` / `git add .` (stage only intended files;
avoids leaking secrets).

### 4. Run the session-start ritual (resolve intent tokens via the manifest)
- `sync_repos` -> update each repo in `manifest.repos` that has a `remote` (use RELATIVE
  paths from `manifest.paths.root`); skip local-only repos.
- `read_conventions` -> read collab `CONVENTIONS.md` + `COORDINATION.md`.
- `check_handoffs` -> search `_handoff/` for items addressed to you or `all` with open status.
- `check_backlog` -> resolve `manifest.backlog` (a file read, or an issue-tracker query).

### 5. Do the work, re-checking capabilities each step
Claim a backlog item -> branch -> work -> report to the allowed write scope (e.g. findings/)
-> commit with your prefix -> open a PR if `open_pr` is allowed (else hand off). Re-read
`persona.yaml` if you are unsure whether an action is permitted.

### 6. Hand off + close
Drop a `_handoff/` if another persona is needed; update the backlog item status.

---

## Self-audit prompt (paste into your working notes)

```
I am <persona>. My git identity is <git_name> <git_email>, prefix <commit_prefix>.
I MAY: <allow verbs>
I MUST NOT: <deny verbs + denied write scopes>
Before each action I will confirm it is in MAY and not in MUST NOT.
If unsure, I deny myself and hand off to the owner.
```

## Why Tier 1 still works (do not skip it)

- It is the only universal path - proves the canon is truly runtime-neutral.
- Instruction-only guardrails caught real junk in the Phase 2 dogfood (the "never git add -A"
  catch). Discipline is a real control, not a placeholder.
- A Tier-3 runtime degrading to Tier 1 (e.g. sub-agents unavailable) can still operate every
  persona correctly by following this file. Graceful degradation, guaranteed.

## What this adapter does NOT do

- It emits no persistent artifact. If the runtime later gains Tier 2/3 support, switch to that
  adapter to gain enforcement / persistence. Tier 1 is correct, not optimal.