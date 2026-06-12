#!/usr/bin/env bash
#
# collect_git_metrics.sh — read-only git metric collection for the
# multi-agent-audit skill. Touches no state in the audited repo.
#
# Usage:
#   ./collect_git_metrics.sh <repo-path> <window-start-YYYY-MM-DD> [window-end-YYYY-MM-DD]
#
# Environment variables:
#   CONV_COMMITS_FILTER=1   (default: 1)
#     When set, the script separately buckets Conventional Commits types
#     (feat, fix, docs, chore, refactor, test, ci, style, perf, build,
#     revert) into commits_by_conv_commit_type, leaving commits_by_persona_prefix
#     for actual agent persona prefixes only. Disable with CONV_COMMITS_FILTER=0
#     if your project uses persona prefixes that overlap conv-commits keywords.
#   PERSONA_PREFIXES="iris,dave,kris,vera,ivy"
#     Comma-separated list of persona slugs to recognize as prefixes.
#     If unset, ALL non-conv-commit prefixes that look like persona slugs
#     are accepted. Setting this explicitly produces cleaner output.
#
# Output: machine-readable JSON to stdout.
#
# Portability: bash 3.2+ (no associative arrays — macOS ships bash 3.2 by
# default and Apple does not ship bash 4+). All aggregation is done in awk,
# which has portable associative arrays.
#
# Hard rules:
#   - This script ONLY runs read-only git commands: log, shortlog, rev-parse.
#     It never commits, pushes, fetches, or modifies any state in the audited
#     repo.
#   - It uses `git -C <repo>` exclusively, so it never cd's into the audited
#     repo (the auditor's working directory stays outside).
#   - If a query is not safe or not available, the script emits the field
#     with the value null and a reason in the notes array.

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
CONV_COMMITS_FILTER="${CONV_COMMITS_FILTER:-1}"
PERSONA_PREFIXES="${PERSONA_PREFIXES:-}"

if [ ! -d "$REPO/.git" ]; then
    echo "error: $REPO is not a git repository" >&2
    exit 1
fi

# Guard rail: refuse to run inside the audited repo (the auditor's working
# directory should stay outside).
REPO_REAL="$(cd "$REPO" 2>/dev/null && pwd -P)"
PWD_REAL="$(pwd -P)"
if [ "$PWD_REAL" = "$REPO_REAL" ]; then
    echo "error: invoke from outside the audited repo (pwd == repo path)" >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

# Compute window length in days, portable across macOS BSD date and GNU date.
window_days() {
    local start="$1" end="$2"
    if date -u -j -f "%Y-%m-%d" "$start" "+%s" >/dev/null 2>&1; then
        # macOS / BSD date
        local s e
        s=$(date -u -j -f "%Y-%m-%d" "$start" "+%s")
        e=$(date -u -j -f "%Y-%m-%d" "$end" "+%s")
        echo $(( (e - s) / 86400 ))
    else
        # GNU date (Linux)
        local s e
        s=$(date -u -d "$start" "+%s")
        e=$(date -u -d "$end" "+%s")
        echo $(( (e - s) / 86400 ))
    fi
}

WINDOW_DAYS=$(window_days "$WINDOW_START" "$WINDOW_END")
[ "$WINDOW_DAYS" -lt 1 ] && WINDOW_DAYS=1

# -----------------------------------------------------------------------------
# 1. Per-actor commit attribution (persona-prefix-aware), in awk.
# -----------------------------------------------------------------------------
#
# Output of this awk pass: a temp file with one line per actor in the form
#   KIND|name|count
# where KIND is "persona" (commits attributed via persona prefix like "iris:")
# or "author" (commits attributed via git author name when no prefix matched).

ACTOR_TMP=$(mktemp -t mam-actor.XXXXXX)
trap 'rm -f "$ACTOR_TMP" "$LINES_TMP" 2>/dev/null' EXIT

git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges \
    --format='COMMIT|%H|%an|%s' 2>/dev/null \
| CONV_COMMITS_FILTER="$CONV_COMMITS_FILTER" PERSONA_PREFIXES="$PERSONA_PREFIXES" awk -F'|' '
    BEGIN {
        # Conventional Commits keywords — when CONV_COMMITS_FILTER=1, these
        # are bucketed separately so they do not pollute persona attribution.
        cc_filter = ENVIRON["CONV_COMMITS_FILTER"];
        if (cc_filter == "") cc_filter = "1";
        split("feat,fix,docs,chore,refactor,test,ci,style,perf,build,revert", cc_arr, ",");
        for (i in cc_arr) cc_types[cc_arr[i]] = 1;

        # Explicit persona allow-list (optional). If set, only these prefixes
        # are accepted as personas; everything else goes to "other" bucket.
        allow_personas = ENVIRON["PERSONA_PREFIXES"];
        has_allow_list = 0;
        if (allow_personas != "") {
            has_allow_list = 1;
            split(allow_personas, p_arr, ",");
            for (i in p_arr) {
                gsub(/^ +| +$/, "", p_arr[i]);
                allowed[tolower(p_arr[i])] = 1;
            }
        }
    }
    /^COMMIT/ {
        author = $3;
        # First "token" of the subject before a colon, lowercased, must be
        # short (<= 30 chars) and contain no spaces.
        subject = $4;
        # Concatenate any extra fields back together (defensive against |
        # appearing in commit subjects).
        for (i = 5; i <= NF; i++) subject = subject "|" $i;
        colon = index(subject, ":");
        if (colon > 0 && colon <= 31) {
            prefix = tolower(substr(subject, 1, colon - 1));
            # Reject anything with spaces or punctuation we do not expect.
            if (prefix !~ /^[a-z0-9_-]+$/) prefix = "";
        } else {
            prefix = "";
        }

        if (prefix == "") {
            # No prefix at all → attributed to author identity
            author_count[author]++;
        } else if (cc_filter == "1" && (prefix in cc_types)) {
            # Conventional-commits type → separate bucket, plus author attribution
            conv_count[prefix]++;
            author_count[author]++;
        } else if (has_allow_list && !(prefix in allowed)) {
            # Persona allow-list active and this prefix is not in it
            # → unrecognized prefix; attribute to author and note
            other_prefix_count[prefix]++;
            author_count[author]++;
        } else {
            # Legitimate persona prefix
            persona_count[prefix]++;
        }
    }
    END {
        for (k in persona_count) print "persona|" k "|" persona_count[k];
        for (k in conv_count) print "conv|" k "|" conv_count[k];
        for (k in other_prefix_count) print "other|" k "|" other_prefix_count[k];
        for (k in author_count) print "author|" k "|" author_count[k];
    }
' > "$ACTOR_TMP"

# -----------------------------------------------------------------------------
# 2. Per-author lines added / removed (shortstat aggregation in awk).
# -----------------------------------------------------------------------------

LINES_TMP=$(mktemp -t mam-lines.XXXXXX)

git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --shortstat \
    --format='AUTHOR|%an' 2>/dev/null \
| awk '
    /^AUTHOR\|/ {
        sub(/^AUTHOR\|/, "");
        current = $0;
        next;
    }
    /file.* changed/ {
        ins = 0; del = 0;
        if (match($0, /[0-9]+ insertion/)) {
            n = substr($0, RSTART, RLENGTH);
            gsub(/[^0-9]/, "", n);
            ins = n + 0;
        }
        if (match($0, /[0-9]+ deletion/)) {
            n = substr($0, RSTART, RLENGTH);
            gsub(/[^0-9]/, "", n);
            del = n + 0;
        }
        inserts[current] += ins;
        deletes[current] += del;
    }
    END {
        for (a in inserts) print a "|" inserts[a] "|" deletes[a];
    }
' > "$LINES_TMP"

# -----------------------------------------------------------------------------
# 3. Totals
# -----------------------------------------------------------------------------

TOTAL_COMMITS=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --oneline 2>/dev/null | wc -l | tr -d ' ')

TOTAL_MERGES=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --merges --oneline 2>/dev/null | wc -l | tr -d ' ')

ACTIVE_DAYS=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --format='%ad' --date=short 2>/dev/null \
    | sort -u | wc -l | tr -d ' ')

# -----------------------------------------------------------------------------
# 4. Rework signals
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

FIX_PREFIX_COUNT=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --grep='^fix:\|^chore: fix\|^refactor: fix' --oneline 2>/dev/null | wc -l | tr -d ' ')

# Rework rate (avoid div-by-zero)
REWORK_DENOM=$TOTAL_COMMITS
[ "$REWORK_DENOM" -eq 0 ] && REWORK_DENOM=1
REWORK_RATE=$(awk "BEGIN { printf \"%.4f\", ($REVERT_COUNT + $HOTFIX_COUNT + $FIXUP_COUNT) / $REWORK_DENOM }")

# -----------------------------------------------------------------------------
# 5. Large-commit proxy (>= 20 files changed) — proxy for `git add -A` use
# -----------------------------------------------------------------------------

LARGE_COMMITS=$(git -C "$REPO" log \
    --since="$WINDOW_START" --until="$WINDOW_END 23:59:59" \
    --no-merges --shortstat --format='COMMIT|%H' 2>/dev/null \
    | awk '
        /^COMMIT/ { next }
        /files? changed/ {
            if (match($0, /[0-9]+ files? changed/)) {
                n = substr($0, RSTART, RLENGTH);
                gsub(/[^0-9]/, "", n);
                if (n + 0 >= 20) c++;
            }
        }
        END { print c + 0 }
    ')

# -----------------------------------------------------------------------------
# 6. JSON emission
# -----------------------------------------------------------------------------

# JSON-escape via sed: backslashes, quotes, tabs, control chars stripped.
json_escape() {
    printf '%s' "$1" \
        | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
        | tr -d '\n\r'
}

# Emit a JSON object body from a temp-file where each line is "key|value".
# Numeric values are emitted unquoted; quoting is the caller's responsibility
# for non-numeric.
emit_kv_object_from_file() {
    local file="$1" kind="$2"  # kind: persona | author | lines
    local first=1
    while IFS='|' read -r f1 f2 f3; do
        [ -z "$f1" ] && continue
        if [ "$kind" = "lines" ]; then
            # f1=author, f2=ins, f3=del
            [ "$first" -eq 1 ] && first=0 || printf ",\n"
            printf '    "%s": { "insertions": %d, "deletions": %d }' \
                "$(json_escape "$f1")" "$f2" "$f3"
        else
            # persona/author: f1=kind, f2=name, f3=count   (caller filters first column)
            if [ "$f1" = "$kind" ]; then
                [ "$first" -eq 1 ] && first=0 || printf ",\n"
                printf '    "%s": %d' "$(json_escape "$f2")" "$f3"
            fi
        fi
    done < "$file"
    printf "\n"
}

echo "{"
printf '  "script": "collect_git_metrics.sh",\n'
printf '  "version": "1.0",\n'
printf '  "repo": "%s",\n' "$(json_escape "$REPO")"
printf '  "window": {\n'
printf '    "start": "%s",\n' "$WINDOW_START"
printf '    "end": "%s",\n' "$WINDOW_END"
printf '    "days": %d\n' "$WINDOW_DAYS"
printf '  },\n'
printf '  "totals": {\n'
printf '    "commits": %d,\n' "$TOTAL_COMMITS"
printf '    "merges": %d,\n' "$TOTAL_MERGES"
printf '    "active_days": %d,\n' "$ACTIVE_DAYS"
printf '    "large_commits_proxy": %d\n' "$LARGE_COMMITS"
printf '  },\n'
printf '  "rework": {\n'
printf '    "reverts": %d,\n' "$REVERT_COUNT"
printf '    "hotfixes": %d,\n' "$HOTFIX_COUNT"
printf '    "fixups": %d,\n' "$FIXUP_COUNT"
printf '    "fix_prefix": %d,\n' "$FIX_PREFIX_COUNT"
printf '    "rework_rate": %s\n' "$REWORK_RATE"
printf '  },\n'

printf '  "commits_by_persona_prefix": {\n'
emit_kv_object_from_file "$ACTOR_TMP" "persona"
printf '  },\n'

printf '  "commits_by_conv_commit_type": {\n'
emit_kv_object_from_file "$ACTOR_TMP" "conv"
printf '  },\n'

printf '  "commits_by_other_prefix": {\n'
emit_kv_object_from_file "$ACTOR_TMP" "other"
printf '  },\n'

printf '  "commits_by_author": {\n'
emit_kv_object_from_file "$ACTOR_TMP" "author"
printf '  },\n'

printf '  "lines_by_author": {\n'
emit_kv_object_from_file "$LINES_TMP" "lines"
printf '  },\n'

printf '  "config": {\n'
printf '    "conv_commits_filter": %s,\n' "$([ "$CONV_COMMITS_FILTER" = "1" ] && echo true || echo false)"
printf '    "persona_prefixes_allowlist": "%s"\n' "$(json_escape "$PERSONA_PREFIXES")"
printf '  },\n'

printf '  "notes": [\n'
printf '    "Persona-prefix attribution honors first colon-separated token of commit subject (case-insensitive, no spaces, [a-z0-9_-] only).",\n'
printf '    "Conventional Commits types (feat/fix/docs/chore/refactor/test/ci/style/perf/build/revert) bucketed separately when CONV_COMMITS_FILTER=1 (the default).",\n'
printf '    "When PERSONA_PREFIXES is set, only those prefixes count as personas; other recognized prefixes go to commits_by_other_prefix.",\n'
printf '    "Commits without a recognized persona prefix attributed by author name. With CONV_COMMITS_FILTER=1, conv-commit-typed commits ALSO contribute to commits_by_author so totals reconcile.",\n'
printf '    "Reverts/hotfixes/fixups counted by grep over commit messages; refine for false positives in the auditor.",\n'
printf '    "Large-commit proxy (>=20 files) is a weak signal for git add -A use; treat as inferred.",\n'
printf '    "Portable: bash 3.2+ (no associative arrays; aggregation done in awk)."\n'
printf '  ]\n'
echo "}"
