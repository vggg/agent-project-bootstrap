## Recent changes
<!-- 3 entries max, most recent first -->

---

# Vault Conventions

Vault-wide rules that all agents follow. Canonical source for tool hierarchy and wikilink format.

## Vault tools

| Task | Tool |
|---|---|
| Read a vault file | `Read` |
| Write or create a vault file | `Write` or `Edit` |
| Search vault content | `Bash` with `grep -r` or `find` |
| Git operations on the vault | `Bash` |
| Obsidian MCP (`mcp__obsidian__*`) | **Never. Not available.** |

Always write vault files directly to `{{VAULT_PATH}}/...` using Read/Write/Edit tools.

## Wikilinks

Use `[[filename]]` wikilinks only in vault files (`.md` inside `{{VAULT_PATH}}`). Never use wikilinks in workspace CLAUDE.md files — absolute paths only there.

When linking to a note, use the filename without extension: `[[my-note]]` not `[[my-note.md]]`.

## Contradictory rules

If two config files appear to contradict, the more specific file wins:

**workspace CLAUDE.md > COORDINATION.md > _meta/CONVENTIONS.md**

If still ambiguous after applying this order, write a handoff to Iris with `priority: high` and stop work on the affected area until the user resolves it.
