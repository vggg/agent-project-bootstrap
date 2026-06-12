#!/usr/bin/env python3
"""
persona_attribution.py — Per-persona PR attribution via the multi-substrate lens.

For each declared persona, join its identity substrates and produce a usage
profile: issues claimed via `agent-<slug>` label, PRs closing those issues,
files touched by those PRs, lines added/removed, and the persona's observed
write-area vs declared write-area.

This is the v1.3 fix for the "identity collision in git log" finding from the
v1.2.0 GardenTwin audit — the multi-substrate truth is recoverable; this script
recovers it.

Usage:
  python3 persona_attribution.py \\
    --repo <owner>/<name> \\
    --window-start <YYYY-MM-DD> \\
    [--window-end <YYYY-MM-DD>] \\
    --personas iris,dave,kris,vera,ivy \\
    [--declared-write-areas <yaml-or-json-file>] \\
    [--format json|md]

Requires `gh` CLI authenticated. Uses gh + git for the joins.
Read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path


def gh(args: list[str]) -> str:
    """Run gh; return stdout."""
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return r.stdout


def gh_json(args: list[str]):
    out = gh(args)
    try:
        return json.loads(out) if out.strip() else None
    except json.JSONDecodeError:
        return None


def list_issues_for_persona(repo: str, persona: str, start: str, end: str) -> list[dict]:
    args = [
        "issue", "list",
        "--repo", repo,
        "--state", "all",
        "--limit", "1000",
        "--label", f"agent-{persona}",
        "--search", f"created:>={start} created:<={end}",
        "--json", "number,title,createdAt,closedAt,labels,state",
    ]
    data = gh_json(args)
    return data if isinstance(data, list) else []


def extract_closes_from_body(body: str) -> list[int]:
    """Find Closes #N / Fixes #N / Resolves #N references in PR body."""
    if not body:
        return []
    matches = re.findall(r"(?i)\b(?:closes|fixes|resolves)\s+#(\d+)", body)
    return [int(m) for m in matches]


def list_prs_in_window(repo: str, start: str, end: str) -> list[dict]:
    args = [
        "pr", "list",
        "--repo", repo,
        "--state", "merged",
        "--limit", "1000",
        "--search", f"merged:>={start} merged:<={end}",
        "--json", "number,title,body,author,mergedAt,additions,deletions,files",
    ]
    data = gh_json(args)
    return data if isinstance(data, list) else []


def attribute(repo: str, persona: str, claimed_issue_nums: set[int], prs: list[dict]) -> dict:
    """For a persona, find PRs that closed their claimed issues + aggregate."""
    matched_prs = []
    total_additions = total_deletions = 0
    files_touched = defaultdict(int)  # path → number of PRs touching it

    for pr in prs:
        closes = extract_closes_from_body(pr.get("body", "") or "")
        if any(n in claimed_issue_nums for n in closes):
            matched_prs.append({
                "number": pr.get("number"),
                "title": (pr.get("title") or "")[:120],
                "closes_issues": [n for n in closes if n in claimed_issue_nums],
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "merged_at": pr.get("mergedAt"),
            })
            total_additions += pr.get("additions", 0) or 0
            total_deletions += pr.get("deletions", 0) or 0
            for f in (pr.get("files") or []):
                fpath = f.get("path") if isinstance(f, dict) else None
                if fpath:
                    files_touched[fpath] += 1

    # Roll up file paths to top-level directories for write-area comparison
    top_dirs = defaultdict(int)
    for path, count in files_touched.items():
        parts = path.split("/")
        if len(parts) >= 2:
            top_dirs[f"{parts[0]}/{parts[1]}/"] += count
        else:
            top_dirs[parts[0]] += count

    return {
        "persona": persona,
        "issues_claimed": len(claimed_issue_nums),
        "prs_closing_claimed_issues": len(matched_prs),
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "files_touched_distinct": len(files_touched),
        "top_directories": dict(sorted(top_dirs.items(), key=lambda kv: -kv[1])[:10]),
        "prs": matched_prs,
    }


def load_declared_write_areas(path: Path) -> dict[str, list[str]]:
    """Load declared write_areas from a YAML or JSON file.

    Expected shape (JSON):
      {"dave": ["src/**", "tests/**"], "vera": ["projects/.../ClaudeAnalyst/**"], ...}

    For YAML (PyYAML may not be installed), we punt and only accept JSON in v1.3.
    """
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def check_write_area_compliance(observed_dirs: dict[str, int], declared: list[str]) -> dict:
    """Compare observed top directories against declared globs."""
    if not declared:
        return {"declared_count": 0, "compliant": None, "note": "no declared write_areas to check"}
    # Crude prefix-match (full glob handling deferred)
    compliant_count = 0
    out_of_scope = []
    for d, count in observed_dirs.items():
        any_match = any(d.startswith(decl.split("/**")[0]) for decl in declared)
        if any_match:
            compliant_count += count
        else:
            out_of_scope.append({"dir": d, "touches": count})
    total = sum(observed_dirs.values()) or 1
    return {
        "declared_count": len(declared),
        "compliant_pct": round(100.0 * compliant_count / total, 1),
        "out_of_scope": out_of_scope,
    }


def render_md(results: list[dict]) -> str:
    lines = [
        "### Per-persona PR attribution (multi-substrate lens)",
        "",
        "| Persona | Issues claimed | PRs closing those | Additions | Deletions | Distinct files | Top dir |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        top_dir = next(iter(r["top_directories"])) if r["top_directories"] else "—"
        lines.append(
            f"| {r['persona']} | {r['issues_claimed']} | {r['prs_closing_claimed_issues']} | "
            f"+{r['total_additions']} | -{r['total_deletions']} | "
            f"{r['files_touched_distinct']} | {top_dir} |"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--window-start", required=True)
    ap.add_argument("--window-end", default=date.today().isoformat())
    ap.add_argument("--personas", required=True, help="Comma-separated persona slugs")
    ap.add_argument("--declared-write-areas", type=Path, default=None,
                    help="Optional JSON file mapping persona slug → list of glob patterns")
    ap.add_argument("--format", choices=("json", "md"), default="md")
    args = ap.parse_args(argv[1:])

    personas = [p.strip().lower() for p in args.personas.split(",") if p.strip()]
    declared_map = load_declared_write_areas(args.declared_write_areas) if args.declared_write_areas else {}

    # Fetch the PR window once
    prs = list_prs_in_window(args.repo, args.window_start, args.window_end)

    results = []
    for persona in personas:
        issues = list_issues_for_persona(args.repo, persona, args.window_start, args.window_end)
        claimed_nums = {i.get("number") for i in issues if i.get("number")}
        res = attribute(args.repo, persona, claimed_nums, prs)
        if persona in declared_map:
            res["write_area_compliance"] = check_write_area_compliance(res["top_directories"], declared_map[persona])
        results.append(res)

    if args.format == "json":
        print(json.dumps({"results": results}, indent=2))
    else:
        print(render_md(results))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
