#!/usr/bin/env bash
# {{PROJECT_NAME}} — workspace setup script
#
# Usage:  ./setup.sh <persona-slug>
#
# Creates ~/Workspace/{{PROJECT_NAME}}/<persona-slug>/ with both repos cloned
# and per-repo git identity configured. Drops a CLAUDE.md (Claude Code) +
# AGENTS.md (code-puppy / others) at the workspace root pointing at the
# canonical agents/<persona>/AGENT.md.
#
# Cron self-registration (for cadence-driven personas like the Librarian) is
# NOT handled here — that's targeted for v0.4.0. For now, register the cron
# manually per the persona's FAILOVER.md / AGENT.md when you're the default
# runner.

set -euo pipefail

PERSONA_SLUG="${1:-}"
if [[ -z "$PERSONA_SLUG" ]]; then
  echo "Usage: $0 <persona-slug>" >&2
  echo "  e.g. $0 librarian" >&2
  exit 1
fi

# Configuration — skill fills these at scaffold time
PROJECT_NAME="{{PROJECT_NAME}}"
CODE_REPO="{{CODE_REPO}}"      # e.g. owner/code-repo
COLLAB_REPO="{{COLLAB_REPO}}"  # e.g. owner/collab-repo
CODE_REPO_DIR="$(basename "$CODE_REPO")"
COLLAB_REPO_DIR="$(basename "$COLLAB_REPO")"

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$HOME/Workspace/$PROJECT_NAME/$PERSONA_SLUG}"

echo "→ Setting up $PERSONA_SLUG workspace at $WORKSPACE_ROOT"
mkdir -p "$WORKSPACE_ROOT"
cd "$WORKSPACE_ROOT"

# Clone both repos if missing (idempotent)
if [[ ! -d "$CODE_REPO_DIR/.git" ]]; then
  echo "→ Cloning $CODE_REPO"
  git clone "git@github.com:$CODE_REPO.git" "$CODE_REPO_DIR"
else
  echo "✓ $CODE_REPO_DIR already cloned"
fi

if [[ ! -d "$COLLAB_REPO_DIR/.git" ]]; then
  echo "→ Cloning $COLLAB_REPO"
  git clone "git@github.com:$COLLAB_REPO.git" "$COLLAB_REPO_DIR"
else
  echo "✓ $COLLAB_REPO_DIR already cloned"
fi

# Read persona identity from the canonical AGENT.md frontmatter
AGENT_MD="$WORKSPACE_ROOT/$COLLAB_REPO_DIR/agents/$PERSONA_SLUG/AGENT.md"
if [[ ! -f "$AGENT_MD" ]]; then
  echo "✗ $AGENT_MD does not exist — persona slug typo, or AGENT.md missing in collab repo" >&2
  exit 1
fi

# Extract persona name + email from frontmatter (simple grep — assumes well-formed YAML)
PERSONA_NAME=$(awk '/^persona:/{print $2; exit}' "$AGENT_MD")
PERSONA_EMAIL=$(awk -F'[`/]' '/^\| Git email/{print $4; exit}' "$AGENT_MD" 2>/dev/null || echo "")
if [[ -z "$PERSONA_NAME" ]]; then
  echo "✗ Could not extract persona name from $AGENT_MD frontmatter" >&2
  exit 1
fi
if [[ -z "$PERSONA_EMAIL" ]]; then
  echo "! Could not extract git email from AGENT.md. Set it manually after this script." >&2
fi

# Configure per-repo git identity
echo "→ Setting git identity in both clones: $PERSONA_NAME / $PERSONA_EMAIL"
for repo_dir in "$CODE_REPO_DIR" "$COLLAB_REPO_DIR"; do
  git -C "$WORKSPACE_ROOT/$repo_dir" config user.name "$PERSONA_NAME"
  if [[ -n "$PERSONA_EMAIL" ]]; then
    git -C "$WORKSPACE_ROOT/$repo_dir" config user.email "$PERSONA_EMAIL"
  fi
done

# Copy workspace bootstrap files (CLAUDE.md for Claude Code, AGENTS.md for code-puppy etc.)
TEMPLATE_DIR="$WORKSPACE_ROOT/$COLLAB_REPO_DIR/workspace-template"
if [[ -d "$TEMPLATE_DIR" ]]; then
  for f in CLAUDE.md AGENTS.md; do
    if [[ -f "$TEMPLATE_DIR/$f" && ! -f "$WORKSPACE_ROOT/$f" ]]; then
      # Simple placeholder substitution
      sed \
        -e "s|{{PERSONA_NAME}}|$PERSONA_NAME|g" \
        -e "s|{{PERSONA_SLUG}}|$PERSONA_SLUG|g" \
        -e "s|{{PERSONA_EMAIL}}|$PERSONA_EMAIL|g" \
        -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" \
        -e "s|{{CODE_REPO}}|$CODE_REPO|g" \
        -e "s|{{COLLAB_REPO}}|$COLLAB_REPO|g" \
        -e "s|{{CODE_REPO_DIR}}|$CODE_REPO_DIR|g" \
        -e "s|{{COLLAB_REPO_DIR}}|$COLLAB_REPO_DIR|g" \
        "$TEMPLATE_DIR/$f" > "$WORKSPACE_ROOT/$f"
      echo "✓ Wrote $WORKSPACE_ROOT/$f"
    fi
  done
else
  echo "! No workspace-template/ in $COLLAB_REPO_DIR — skipping CLAUDE.md/AGENTS.md drop"
fi

echo ""
echo "✓ Workspace ready at $WORKSPACE_ROOT"
echo ""
echo "Next steps:"
echo "  1. cd $WORKSPACE_ROOT"
echo "  2. Open Claude Code (or your AI agent) in this folder"
echo "  3. Read $WORKSPACE_ROOT/$COLLAB_REPO_DIR/agents/$PERSONA_SLUG/AGENT.md"
echo "  4. Follow the persona's session-start ritual"
