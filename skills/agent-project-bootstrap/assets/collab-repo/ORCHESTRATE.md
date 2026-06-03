# ORCHESTRATE — Role 1: Bootstrap a new project (runtime-neutral)

> Recipe for the agent that SETS UP a new multi-agent project. Runtime-neutral; perform every
> concrete action via your runtime's `adapters/<runtime>/HYDRATE.md`. Steps derived from the
> Phase 2 dogfood + friction log (F2/F7/F8 fixes are baked in).

## Inputs you need (ask the user if missing)

- Project name + one-line description.
- The code repo location (existing or to-create) and the collab repo location.
- Backlog source: a file in the collab repo, or an issue tracker.
- The initial persona roster (at least one `dev` persona).

## Steps

### 1. Author `manifest.yaml`
Per `canon/manifest.schema.md`. **Set `paths.strategy: relative`** and express repo paths
relative to the collab root (F7). Pick `backlog.source` honestly — `file` is valid and was
proven in Phase 2 (F8).

### 2. Create the collab repo skeleton
```
collab/
  CONVENTIONS.md      # neutral — capabilities, not tool names (see canon templates)
  COORDINATION.md     # workflow + definition of done
  README.md
  manifest.yaml
  backlog.md          # if backlog.source: file
  _handoff/README.md
  findings/README.md
  agents/<slug>/persona.yaml   # one per persona (canon/persona.schema.md)
```

### 3. Create / prepare the code repo
- Init the code repo if new.
- **Emit a language-appropriate `.gitignore` (F2)** — this is mandatory, it was the #1 ergon
  friction in Phase 2. Include venvs, caches, coverage files, and secret patterns.
- Never `git add -A` during setup (secret hygiene — cross-cutting concern).

### 4. Hydrate each persona
For every entry in `manifest.personas`, run your adapter's HYDRATE steps on its
`persona.yaml`. The adapter:
- maps `capabilities.allow` → the runtime's tool allow-list (enforced layer),
- renders `capabilities.deny` → persona-body "what never happens" (instructed layer),
- renders `session_ritual` tokens → concrete steps using **relative** paths (F7),
- resolves `check_backlog` against `manifest.backlog` (F8),
- emits the commit command (the `/vc-<slug>` analog).

### 5. Derive `AGENT.md` from each `persona.yaml`
Generate the human-readable manual from the yaml (yaml canonical, md derived — F4). Do not
hand-author guardrails in the md.

### 6. Verify the round trip
- Confirm each persona is discoverable + invokable on this runtime (adapter's verify step).
- Confirm relative paths resolve from `paths.root`.
- Open one trivial PR (or commit) through a persona to prove identity + guardrails work.

## Exit

The project is bootstrapped: collab skeleton present, personas hydrated + discoverable,
`.gitignore` in place, one round-trip proven. Hand new joiners to `PARTICIPATE.md`.
