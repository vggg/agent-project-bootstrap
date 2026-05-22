---
name: agent-project-bootstrap
version: 1.0
created: 2026-05-22
---

# Skill: Agent-Project Bootstrap

Generates the vault and workspace CLAUDE.md scaffolding for a new project using the five-agent pattern: Iris (librarian), Dev Agent 1, Dev Agent 2 (optional), Analyst, and Designer.

Use once at project start. After emitting, fill every `{{...}}` placeholder before committing.

## When to use

- Starting a new software project that will use the multi-agent Claude Code setup
- Onboarding a second project into an existing vault

## Emit steps

**1. Create vault directories.**

Inside `{{VAULT_PATH}}`:
- `_meta/PERSONAS/` (if it doesn't exist)
- `projects/{{PROJECT_SLUG}}/`

**2. Copy vault assets.**

```
assets/vault/_meta/CONVENTIONS.md     → {{VAULT_PATH}}/_meta/CONVENTIONS.md
assets/vault/_meta/PERSONAS/*.md      → {{VAULT_PATH}}/_meta/PERSONAS/
assets/vault/CLAUDE.md                → {{VAULT_PATH}}/CLAUDE.md
assets/vault/projects/__PROJECT__/    → {{VAULT_PATH}}/projects/{{PROJECT_SLUG}}/
```

**3. Copy workspace files.**

| Agent | Source | Destination |
|---|---|---|
| Dev 1 | `assets/workspaces/dev/CLAUDE.md` | `{{WORKSPACE_BASE}}/[ProjectDev]/CLAUDE.md` and project repo root |
| Dev 2 *(optional)* | same | `{{WORKSPACE_BASE}}/[ProjectDev-2]/CLAUDE.md` |
| Analyst | `assets/workspaces/analyst/CLAUDE.md` | `{{WORKSPACE_BASE}}/[ProjectAnalyst]/CLAUDE.md` |
| Designer | `assets/workspaces/designer/CLAUDE.md` | `{{WORKSPACE_BASE}}/[ProjectDesigner]/CLAUDE.md` |

Dev 1 and Dev 2 use the same template. If the project uses a shared GitHub repo for both dev workspaces, commit the repo-root CLAUDE.md once — both workspaces pull it.

**4. Fill placeholders.**

Substitute all `{{...}}` tokens. When done, verify none remain:
```bash
grep -r '{{' {{VAULT_PATH}}/projects/{{PROJECT_SLUG}}/ \
  {{VAULT_PATH}}/_meta/ \
  {{WORKSPACE_BASE}}/[Project]*/
```
No output means clean.

**5. Commit vault.**
```bash
git -C {{VAULT_PATH}} add _meta/ projects/{{PROJECT_SLUG}}/
git -C {{VAULT_PATH}} commit -m "iris: init | bootstrap {{PROJECT_NAME}} project"
git -C {{VAULT_PATH}} push
```

**6. Commit repo CLAUDE.md.**

Commit the dev workspace `CLAUDE.md` to the project GitHub repo root.

**7. Log it.**

Prepend to `{{VAULT_PATH}}/wiki/log.md`:
```
## [YYYY-MM-DD] init | Bootstrap {{PROJECT_NAME}} project
Initial vault + workspace scaffolding. Agents: Iris, Dev-1[, Dev-2 (optional)], Analyst, Designer.
```

## Placeholder inventory

| Placeholder | Fill with |
|---|---|
| `{{PROJECT_NAME}}` | Human-readable project name (e.g. "MyProject") |
| `{{PROJECT_SLUG}}` | Lowercase kebab slug (e.g. "myproject") |
| `{{USER_NAME}}` | User's first name — appears in shell command notes |
| `{{VAULT_PATH}}` | Absolute path to the vault root |
| `{{WORKSPACE_BASE}}` | Base directory for all agent workspace clones |
| `{{GITHUB_REPO}}` | `org/repo` slug on GitHub |
| `{{LIVE_URL}}` | Production URL |
| `{{TECH_STACK}}` | Tech stack — brief bullet list or inline prose |
| `{{HOT_FILES}}` | Rows for the hot-files table in COORDINATION.md (tech-stack-specific files) |

## File manifest

```
SKILL.md
references/
  design-decisions.md
  obsidian-setup.md
assets/
  vault/
    _meta/
      CONVENTIONS.md
      PERSONAS/
        IRIS.md
        DAVE.md
        KRIS.md
        VERA.md
        IVY.md
    CLAUDE.md
    projects/__PROJECT__/
      CLAUDE.md
      COORDINATION.md
  workspaces/
    dev/CLAUDE.md
    analyst/CLAUDE.md
    designer/CLAUDE.md
```
