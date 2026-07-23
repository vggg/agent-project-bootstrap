# code-puppy capability map (reconstructed stub)

> **Reconstructed 2026-07-22.** The original note (cited by
> `references/capability-vocab.v1.md § Mapping note` since v1.0) was never committed to this
> repo and could not be located in the vault. The mapping it recorded survives in the adapter
> itself — `assets/collab-repo/adapters/code-puppy/HYDRATE.md` is the maintained,
> machine-checked source of truth (its capability table is parsed by
> `tests/bi_runtime_accept.py`). This stub exists so the citation resolves.

## The abstract → concrete mapping (v1 verbs → code-puppy tools)

| Abstract verb (v1) | code-puppy tools |
|---|---|
| `read_code`, `read_collab` | `read_file`, `list_files`, `grep` |
| `write_code` | `create_file`, `replace_in_file`, `delete_snippet` |
| `write_path: [..]` | `create_file`, `replace_in_file` (scopes instructed in the body) |
| `open_pr`, `run_tests` | `agent_run_shell_command` |
| `merge_pr`, `push_main`, `force_push`, `edit_other_personas` | no dedicated tool — sub-tool of shell/write; denials are instruction-only |
| *(every persona)* | `agent_share_your_reasoning` (narration) |

See `adapters/code-puppy/HYDRATE.md` for the authoritative, normalized table (including
enforcement class per verb) and the hydration steps.
