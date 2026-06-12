#!/usr/bin/env bash
#
# verify_readonly_contract.sh — static checks for the multi-agent-audit skill's
# read-only contract. Run from the skill repo root.
#
# Checks:
#  1. project-auditor subagent file exists at the expected path
#  2. The subagent's tools: frontmatter lists Read, Grep, Glob, Bash, Write
#  3. Edit is NOT listed in tools:
#  4. No script in scripts/ contains `gh api -X` (uppercase or lowercase) for POST/PUT/PATCH/DELETE
#  5. No script contains `git commit`, `git push`, `git tag`, `git reset --hard`, or `git rebase`
#     used against the audited repo (we allow them when output_writer is the audit's own
#     reports repo — but the skill's scripts shouldn't push back to audited repos)
#  6. SKILL.md still contains the read-only rule sentence
#
# Each check prints PASS or FAIL with a one-line reason. Exit code: 0 if all pass.

set -u

SKILL_DIR="${1:-skills/multi-agent-audit}"
PASS=0
FAIL=0

check() {
    local name="$1" status="$2" reason="$3"
    if [ "$status" = "PASS" ]; then
        printf "  ✓ %-50s %s\n" "$name" ""
        PASS=$((PASS + 1))
    else
        printf "  ✗ %-50s %s\n" "$name" "$reason"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== multi-agent-audit read-only contract — static checks ==="
echo "Skill dir: $SKILL_DIR"
echo ""

# Check 1: subagent file exists
SUBAGENT="$SKILL_DIR/agents/project-auditor.md"
if [ -f "$SUBAGENT" ]; then
    check "1. project-auditor.md exists" "PASS" ""
else
    check "1. project-auditor.md exists" "FAIL" "missing: $SUBAGENT"
fi

# Check 2: tools: frontmatter lists Read, Grep, Glob, Bash, Write
TOOLS_LINE=$(grep -E '^tools:' "$SUBAGENT" 2>/dev/null | head -1)
if [ -n "$TOOLS_LINE" ]; then
    EXPECTED_TOOLS=("Read" "Grep" "Glob" "Bash" "Write")
    MISSING=()
    for t in "${EXPECTED_TOOLS[@]}"; do
        echo "$TOOLS_LINE" | grep -q "$t" || MISSING+=("$t")
    done
    if [ ${#MISSING[@]} -eq 0 ]; then
        check "2. tools: includes Read/Grep/Glob/Bash/Write" "PASS" ""
    else
        check "2. tools: includes Read/Grep/Glob/Bash/Write" "FAIL" "missing: ${MISSING[*]}"
    fi
else
    check "2. tools: includes Read/Grep/Glob/Bash/Write" "FAIL" "no tools: line found"
fi

# Check 3: Edit is NOT listed
if [ -n "$TOOLS_LINE" ]; then
    if echo "$TOOLS_LINE" | grep -qE '\bEdit\b'; then
        check "3. Edit is NOT in tools:" "FAIL" "Edit is listed — violates read-only contract"
    else
        check "3. Edit is NOT in tools:" "PASS" ""
    fi
else
    check "3. Edit is NOT in tools:" "FAIL" "no tools: line to inspect"
fi

# Check 4: no destructive gh api in scripts/
DESTRUCTIVE_GH=$(grep -rEn 'gh api .*-X (POST|PUT|PATCH|DELETE)' "$SKILL_DIR/scripts/" 2>/dev/null || true)
if [ -z "$DESTRUCTIVE_GH" ]; then
    check "4. No 'gh api -X POST/PUT/PATCH/DELETE' in scripts/" "PASS" ""
else
    check "4. No 'gh api -X POST/PUT/PATCH/DELETE' in scripts/" "FAIL" "found: $(echo "$DESTRUCTIVE_GH" | head -1)"
fi

# Check 5: no destructive git operations as actual code (not in comments/docstrings)
# - .sh files: grep for raw `git commit/push/...` outside comment lines
# - .py files: grep for subprocess calls invoking those verbs
DESTRUCTIVE_SH=$(grep -rEn '(^|[^a-z])git (commit|push|tag --|rebase|reset --hard|commit --amend)( |$)' \
    "$SKILL_DIR/scripts/" --include="*.sh" 2>/dev/null \
    | grep -vE '^[^:]*:[0-9]+:[[:space:]]*#' || true)
DESTRUCTIVE_PY=$(grep -rEn '(subprocess|os\.system|Popen).*("git"[^,)]*,[[:space:]]*"(commit|push|tag|rebase|reset)"|"(gh)"[^,)]*,[[:space:]]*"(pr|issue)"[^,)]*,[[:space:]]*"(create|merge|edit|close|comment)")' \
    "$SKILL_DIR/scripts/" --include="*.py" 2>/dev/null || true)
DESTRUCTIVE_GIT="$DESTRUCTIVE_SH$DESTRUCTIVE_PY"
if [ -z "$DESTRUCTIVE_GIT" ]; then
    check "5. No destructive git/gh in scripts/ (code, not prose)" "PASS" ""
else
    check "5. No destructive git/gh in scripts/ (code, not prose)" "FAIL" "found: $(echo "$DESTRUCTIVE_GIT" | head -1)"
fi

# Check 6: SKILL.md mentions the read-only principle prominently
# (Accept any of: 'Non-negotiable principle — read-only', 'read-only',
#  'read only', or 'NON-NEGOTIABLE.*read-only' near the top of the file.)
SKILL_FILE="$SKILL_DIR/SKILL.md"
if grep -qiE 'read[-[:space:]]?only' "$SKILL_FILE" 2>/dev/null; then
    check "6. SKILL.md retains read-only language" "PASS" ""
else
    check "6. SKILL.md retains read-only language" "FAIL" "no 'read-only' / 'read only' text found"
fi

echo ""
echo "=== Summary: $PASS pass, $FAIL fail ==="

# Exit 0 only if everything passed
[ $FAIL -eq 0 ]
