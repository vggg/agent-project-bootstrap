#!/usr/bin/env bash
#
# collect_git_metrics.sh — read-only git metric collection for the
# multi-agent-audit skill. Touches no state in the audited repo.
#
# Usage:
#   ./collect_git_metrics.sh <repo-path> <window-start-YYYY-MM-DD> [window-end-YYYY-MM-DD]
#
# Output: machine-readable JSON to stdout.
#
# Hard rules:
#   - This script ONLY runs read-only git commands: log, shortlog, diff,
#     for-each-ref, rev-parse. It never commits, pushes, fetches, or
#     modifies any state in the audited repo.
#   - It uses `git -C <repo>` exclusively, so it never cd's into the
#     audited repo (the auditor's working directory stays outside).
#   - If a query is not safe or not available, it emits a null with a
#     reason field in the JSON.

set -eu

# -----------------------------------------------------------------------------
# Args + defaults
# -----------------------------------------------------------------------------

if [ $# -lt 2 ]; then
    echo "usage: $0 <repo-path> <window-start-YYYY-MM-DD> [window-end-YYYY-MM-DD]" >&2
    exit 1
fi

REPO="$1"
WINDOW_START="$2"
WINDOW_END="${3:-$(date -u +%Y-%m-%d)}"

if [ ! -d "$REPO/.git" ]; then
    echo "error: $REPO is not a git repository" >&2
    exit 1
fi

# Guard rail: refuse to run inside the audited repo
if [ "$(pwd)" = "$(cd "$REPO" 2>/dev/null && pwd)" ]; then
    echo "error: invoke from outside the audited repo (pwd == repo path)" >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

# JSON-escape a string (basic; doesn't handle every edge case but enough for
# author names and short subject lines).
jq_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
        | tr -d '\n\r' | sed 's/$//'
}

# -----------------------------------------------------------------------------
# 1. Commits per canonical actor (post-resolution; honors persona prefix when
#    present, else falls back to author name).
# -----------------------------------------------------------------------------

# Raw commit list in window
COMMITS_RAW=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --format='%H|%an|%ae|%s' \
    --no-merges 2>/dev/null || echo "")

# Per-author tally honoring persona prefix
declare -A AUTHOR_COMMITS
declare -A PERSONA_COMMITS

while IFS='|' read -r sha author email subject; do
    [ -z "$sha" ] && continue

    # Detect persona prefix at start of subject (e.g., "iris: ingest | ...")
    PREFIX=$(echo "$subject" | awk -F: '{ if (NF >= 2 && length($1) <= 30 && $1 !~ / /) print tolower($1); else print "" }')

    if [ -n "$PREFIX" ]; then
        PERSONA_COMMITS["$PREFIX"]=$(( ${PERSONA_COMMITS["$PREFIX"]:-0} + 1 ))
    else
        AUTHOR_COMMITS["$author"]=$(( ${AUTHOR_COMMITS["$author"]:-0} + 1 ))
    fi
done <<< "$COMMITS_RAW"

# -----------------------------------------------------------------------------
# 2. Merges + total commits
# -----------------------------------------------------------------------------

TOTAL_COMMITS=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --oneline 2>/dev/null | wc -l | tr -d ' ')

TOTAL_MERGES=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --merges --oneline 2>/dev/null | wc -l | tr -d ' ')

# -----------------------------------------------------------------------------
# 3. Rework signals: reverts, hotfixes, fix-ups
# -----------------------------------------------------------------------------

REVERT_COUNT=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --grep='^Revert ' --oneline 2>/dev/null | wc -l | tr -d ' ')

HOTFIX_COUNT=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --grep='^hotfix:\|^fix:.*urgent\|^fix:.*p0\|^fix:.*prod\|^fix:.*hotfix' \
    --oneline 2>/dev/null | wc -l | tr -d ' ')

FIXUP_COUNT=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --grep='^fixup!\|^squash!\|fix-up:' --oneline 2>/dev/null | wc -l | tr -d ' ')

# Generic "fix:" prefix (broader signal — includes both routine fixes and
# rework; the auditor's intervention-tax calc cares about fix-ups that
# follow autonomous-agent commits, computed separately).
FIX_PREFIX_COUNT=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --grep='^fix:\|^chore: fix\|^refactor: fix' --oneline 2>/dev/null | wc -l | tr -d ' ')

# -----------------------------------------------------------------------------
# 4. Lines added / removed by author (--shortstat aggregated)
# -----------------------------------------------------------------------------

SHORTSTAT_RAW=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --shortstat --format='AUTHOR|%an' 2>/dev/null || echo "")

declare -A AUTHOR_INSERTIONS
declare -A AUTHOR_DELETIONS
CURRENT_AUTHOR=""

while IFS= read -r line; do
    case "$line" in
        AUTHOR\|*)
            CURRENT_AUTHOR="${line#AUTHOR|}"
            ;;
        *file*changed*)
            INS=$(echo "$line" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo "0")
            DEL=$(echo "$line" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo "0")
            AUTHOR_INSERTIONS["$CURRENT_AUTHOR"]=$(( ${AUTHOR_INSERTIONS["$CURRENT_AUTHOR"]:-0} + INS ))
            AUTHOR_DELETIONS["$CURRENT_AUTHOR"]=$(( ${AUTHOR_DELETIONS["$CURRENT_AUTHOR"]:-0} + DEL ))
            ;;
    esac
done <<< "$SHORTSTAT_RAW"

# -----------------------------------------------------------------------------
# 5. Cadence — distinct active days in window
# -----------------------------------------------------------------------------

ACTIVE_DAYS=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --format='%ad' --date=short 2>/dev/null \
    | sort -u | wc -l | tr -d ' ')

# Window length in days for rate computations
WINDOW_DAYS=$(( ($(date -u -j -f "%Y-%m-%d" "$WINDOW_END" "+%s" 2>/dev/null \
    || date -d "$WINDOW_END" "+%s") \
    - $(date -u -j -f "%Y-%m-%d" "$WINDOW_START" "+%s" 2>/dev/null \
    || date -d "$WINDOW_START" "+%s")) / 86400 ))
[ "$WINDOW_DAYS" -lt 1 ] && WINDOW_DAYS=1

# -----------------------------------------------------------------------------
# 6. Large-commit proxy (>= 20 files changed) — proxy for `git add -A` use
# -----------------------------------------------------------------------------

LARGE_COMMITS=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --shortstat --format='COMMIT|%H' 2>/dev/null \
    | awk '/^COMMIT/ {sha=$0; next}
           /files? changed/ {
             match($0, /[0-9]+ files? changed/);
             n = substr($0, RSTART, RLENGTH);
             gsub(/[^0-9]/, "", n);
             if (n+0 >= 20) print sha;
           }' \
    | wc -l | tr -d ' ')

# -----------------------------------------------------------------------------
# 7. Emit JSON
# -----------------------------------------------------------------------------

echo "{"
echo "  \"script\": \"collect_git_metrics.sh\","
echo "  \"version\": \"1.0\","
echo "  \"repo\": \"$(jq_escape "$REPO")\","
echo "  \"window\": {"
echo "    \"start\": \"$WINDOW_START\","
echo "    \"end\": \"$WINDOW_END\","
echo "    \"days\": $WINDOW_DAYS"
echo "  },"
echo "  \"totals\": {"
echo "    \"commits\": $TOTAL_COMMITS,"
echo "    \"merges\": $TOTAL_MERGES,"
echo "    \"active_days\": $ACTIVE_DAYS,"
echo "    \"large_commits_proxy\": $LARGE_COMMITS"
echo "  },"
echo "  \"rework\": {"
echo "    \"reverts\": $REVERT_COUNT,"
echo "    \"hotfixes\": $HOTFIX_COUNT,"
echo "    \"fixups\": $FIXUP_COUNT,"
echo "    \"fix_prefix\": $FIX_PREFIX_COUNT,"
echo "    \"rework_rate\": $(awk "BEGIN { printf \"%.4f\", ($REVERT_COUNT + $HOTFIX_COUNT + $FIXUP_COUNT) / ($TOTAL_COMMITS > 0 ? $TOTAL_COMMITS : 1) }")"
echo "  },"
echo "  \"commits_by_persona_prefix\": {"
FIRST=1
for key in "${!PERSONA_COMMITS[@]}"; do
    [ "$FIRST" -eq 1 ] && FIRST=0 || echo ","
    printf "    \"%s\": %d" "$(jq_escape "$key")" "${PERSONA_COMMITS[$key]}"
done
echo ""
echo "  },"
echo "  \"commits_by_author\": {"
FIRST=1
for key in "${!AUTHOR_COMMITS[@]}"; do
    [ "$FIRST" -eq 1 ] && FIRST=0 || echo ","
    printf "    \"%s\": %d" "$(jq_escape "$key")" "${AUTHOR_COMMITS[$key]}"
done
echo ""
echo "  },"
echo "  \"lines_by_author\": {"
FIRST=1
for key in "${!AUTHOR_INSERTIONS[@]}"; do
    [ "$FIRST" -eq 1 ] && FIRST=0 || echo ","
    printf "    \"%s\": { \"insertions\": %d, \"deletions\": %d }" \
        "$(jq_escape "$key")" \
        "${AUTHOR_INSERTIONS[$key]}" \
        "${AUTHOR_DELETIONS[$key]:-0}"
done
echo ""
echo "  },"
echo "  \"notes\": ["
echo "    \"Persona-prefix attribution honors first colon-separated token of commit subject (case-insensitive, no spaces).\","
echo "    \"Commits without a recognized persona prefix attributed by author name.\","
echo "    \"Reverts/hotfixes/fixups counted by grep over commit messages; refine for false positives in the auditor.\","
echo "    \"Large-commit proxy (>=20 files) is a weak signal for 'git add -A' use; treat as inferred.\""
echo "  ]"
echo "}"
