# CORRECTION — Wibey vs. code-puppy (reconstructed stub)

> **Reconstructed 2026-07-22.** The original note (cited by
> `adapters/code-puppy/HYDRATE.md` since v1.0) was never committed to this repo and could not
> be located in the vault. This stub captures what the citation claims the note contains, from
> the adapter text and the ADR-001 §2.4 context. Treat details beyond these as lost.

## What the original recorded

During the Phase 1 adapter spike, the work runtime was initially assumed to behave like
**Wibey**; verification against the actual runtime — **code-puppy** — corrected several
assumptions. The adapter's claims were verified against code-puppy source
(`code_puppy/agents/json_agent.py`, `code_puppy/tools/__init__.py`, `code_puppy/config.py`)
and a live `list_agents` + `invoke_agent` round trip:

- **Enforcement is real but partial.** `JSONAgent.get_available_tools()` filters the agent
  JSON's `tools` list against the live `TOOL_REGISTRY` — only listed tools are registered.
  Whole-tool denials are therefore hard-enforced; sub-tool denials (inside a granted shell or
  write tool) remain instruction-only.
- **`model` IS applied on code-puppy** (pins the agent's model) — unlike Wibey, where the
  field was observed to be ignored.
- **There is no `permissionMode` field** in code-puppy's agent JSON schema.
- Path quirk: agents/config live under `~/.code_puppy/` (underscore); custom commands under
  `~/.code-puppy/commands/` (hyphen). Project-scoped: `{repo}/.code_puppy/agents/` and
  `{repo}/.agents/commands/`.

## Why it mattered

The correction is the provenance for the code-puppy adapter's enforcement-boundary table
(`adapters/code-puppy/HYDRATE.md § Enforcement boundary`) and for LEARNINGS L2
(enforceability is a property of the runtime, not the capability).
