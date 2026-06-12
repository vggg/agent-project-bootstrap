#!/usr/bin/env python3
"""
extract_timeline.py — Extract important events from a multi-agent project's repos.

Emits the §9.5 Timeline section for the audit report. Event taxonomy + importance
heuristic per `references/timeline.md`.

Usage:
  python3 extract_timeline.py \\
    --repo <code-repo-path> \\
    [--coordination <coordination-or-vault-path>] \\
    --window-start <YYYY-MM-DD> \\
    [--window-end <YYYY-MM-DD>] \\
    [--format md|json] \\
    [--all]                         # include events with importance < 4

Read-only. Uses only git log / git tag / file inspection. No git fetch.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass
class Event:
    date: str       # YYYY-MM-DD
    type: str       # release | adr | adr_accepted | roster | convention | incident | audit | feature | start | end
    title: str
    importance: int  # 1-10
    source: str


# ---- event detectors ----------------------------------------------------

CONV_FILE_PATTERNS = ("CONVENTIONS.md", "COORDINATION.md")
INCIDENTS_DIR_NAMES = ("incidents", "INCIDENTS")
RESTRUCTURE_KEYWORDS = ("restructure", "role-update", "on-leave", "team-change", "roster", "workforce")


def git(args: list[str], cwd: Path) -> str:
    """Run a git command read-only; return stdout (decoded)."""
    out = subprocess.run(["git", "-C", str(cwd)] + args, capture_output=True, text=True)
    return out.stdout


def in_window(d: str, start: str, end: str) -> bool:
    return start <= d <= end


def detect_project_creation(repo: Path, start: str, end: str) -> list[Event]:
    out = git(["log", "--reverse", "--format=%ad|%H|%s", "--date=short"], repo)
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) >= 3:
            d, sha, subj = parts[0], parts[1], parts[2]
            if in_window(d, start, end):
                return [Event(d, "start", "Project repo first commit", 6, f"git {sha[:7]}")]
            break  # first commit is outside window; not in scope
    return []


def detect_release_tags(repo: Path, start: str, end: str) -> list[Event]:
    out = git(["tag", "--sort=creatordate", "--format=%(refname:short)|%(creatordate:short)"], repo)
    events = []
    for line in out.splitlines():
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        tag, d = parts[0], parts[1]
        if not re.match(r"^v?\d+\.\d+\.\d+", tag):
            continue
        if in_window(d, start, end):
            # Major if X.0.0, otherwise minor/patch
            m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", tag)
            major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if minor == 0 and patch == 0:
                importance = 8
            elif patch == 0:
                importance = 6
            else:
                importance = 4
            events.append(Event(d, "release", f"Release {tag}", importance, f"tag {tag}"))
    return events


def detect_adr_creations(repo: Path, start: str, end: str) -> list[Event]:
    # New ADR files added in the window
    out = git(
        ["log", "--since=" + start, "--until=" + end + " 23:59:59",
         "--diff-filter=A", "--name-only", "--format=COMMIT|%ad|%s", "--date=short"],
        repo,
    )
    events = []
    current_date, current_subj = None, None
    for line in out.splitlines():
        if line.startswith("COMMIT|"):
            parts = line.split("|", 2)
            current_date = parts[1] if len(parts) > 1 else None
            current_subj = parts[2] if len(parts) > 2 else None
            continue
        if not line.strip():
            continue
        # Match ADR files under docs/adr/ or projects/<x>/decisions/
        path = line.strip()
        if re.search(r"docs/adr/ADR-\d+", path) and current_date:
            slug = Path(path).stem
            events.append(Event(current_date, "adr", f"{slug} filed", 5, path))
    return events


def detect_convention_changes(repo: Path, start: str, end: str) -> list[Event]:
    events = []
    for fname in CONV_FILE_PATTERNS:
        out = git(
            ["log", "--since=" + start, "--until=" + end + " 23:59:59",
             "--format=%ad|%H|%s", "--date=short", "--shortstat", "--", fname],
            repo,
        )
        # Process pairs (header + shortstat) of git log --shortstat output
        lines = out.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            parts = line.split("|", 2)
            if len(parts) >= 3:
                d, sha, subj = parts[0], parts[1], parts[2]
                # Look ahead for the shortstat line
                changed_lines = 0
                if i + 1 < len(lines) and "changed" in lines[i + 1]:
                    m = re.search(r"(\d+) insertion", lines[i + 1])
                    if m: changed_lines += int(m.group(1))
                    m = re.search(r"(\d+) deletion", lines[i + 1])
                    if m: changed_lines += int(m.group(1))
                    i += 2
                else:
                    i += 1
                if in_window(d, start, end) and changed_lines > 0:
                    importance = 5 if changed_lines > 50 else 3
                    events.append(Event(d, "convention",
                                        f"{fname} change ({changed_lines} lines)",
                                        importance,
                                        f"git {sha[:7]} {fname}"))
            else:
                i += 1
    return events


def detect_incidents(repo: Path, start: str, end: str) -> list[Event]:
    # Reverts to main
    out = git(
        ["log", "--since=" + start, "--until=" + end + " 23:59:59",
         "--grep=^Revert ", "--format=%ad|%H|%s", "--date=short"],
        repo,
    )
    events = []
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3 and in_window(parts[0], start, end):
            events.append(Event(parts[0], "incident", f"Revert: {parts[2][:80]}", 6, f"git {parts[1][:7]}"))
    # Hotfix-cluster heuristic: ≥3 fix: commits within 4 hours on main
    out2 = git(
        ["log", "--since=" + start, "--until=" + end + " 23:59:59",
         "--grep=^fix:\\|^hotfix:\\|^fix\\(", "--format=%aI|%H|%s"],
        repo,
    )
    fix_times = []
    for line in out2.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            try:
                ts = datetime.fromisoformat(parts[0].replace("Z", "+00:00"))
                fix_times.append((ts, parts[1], parts[2]))
            except ValueError:
                continue
    fix_times.sort()
    for i in range(len(fix_times) - 2):
        ts1, _, _ = fix_times[i]
        ts3, sha3, subj3 = fix_times[i + 2]
        if (ts3 - ts1) <= timedelta(hours=4):
            d = ts1.date().isoformat()
            if in_window(d, start, end):
                events.append(Event(d, "incident",
                                    f"Hotfix cluster (≥3 fix-commits in 4h, e.g. {subj3[:60]})",
                                    5, f"git cluster ending {sha3[:7]}"))
    return events


def detect_audit_snapshots(audit_dir: Path | None, start: str, end: str) -> list[Event]:
    if not audit_dir:
        return []
    snap_dir = audit_dir / "snapshots"
    if not snap_dir.exists():
        return []
    events = []
    for p in sorted(snap_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            ts = (data.get("audit_run") or {}).get("timestamp")
            if ts:
                d = ts[:10]
                if in_window(d, start, end):
                    events.append(Event(d, "audit", f"Audit snapshot ({p.name})", 4, str(p)))
        except Exception:
            continue
    return events


def detect_large_features(repo: Path, start: str, end: str, line_threshold: int = 500) -> list[Event]:
    """PR squash-merges that landed ≥line_threshold lines in a single commit on main."""
    out = git(
        ["log", "--first-parent", "main",
         "--since=" + start, "--until=" + end + " 23:59:59",
         "--no-merges",
         "--format=%ad|%H|%s", "--date=short", "--shortstat"],
        repo,
    )
    events = []
    lines = out.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        parts = line.split("|", 2)
        if len(parts) >= 3:
            d, sha, subj = parts[0], parts[1], parts[2]
            changed_lines = 0
            if i + 1 < len(lines) and "changed" in lines[i + 1]:
                m = re.search(r"(\d+) insertion", lines[i + 1])
                if m: changed_lines += int(m.group(1))
                m = re.search(r"(\d+) deletion", lines[i + 1])
                if m: changed_lines += int(m.group(1))
                i += 2
            else:
                i += 1
            if changed_lines >= line_threshold and in_window(d, start, end):
                importance = 5 if changed_lines >= 1000 else 4
                events.append(Event(d, "feature",
                                    f"Large change: {subj[:80]} ({changed_lines} lines)",
                                    importance,
                                    f"git {sha[:7]}"))
        else:
            i += 1
    return events


def detect_roster_changes(coordination: Path | None, start: str, end: str) -> list[Event]:
    """Look in _handoff/ files for restructure/role-update/on-leave handoffs.

    Coordination repos that aren't git-tracked: fall back to file mtimes.
    """
    if not coordination:
        return []
    handoff_dir = coordination / "_handoff"
    if not handoff_dir.exists():
        return []
    events = []
    for p in sorted(handoff_dir.glob("*.md")):
        try:
            content = p.read_text(errors="replace")
        except Exception:
            continue
        head = content[:1500].lower()
        name_lower = p.name.lower()
        if any(k in head for k in RESTRUCTURE_KEYWORDS) or any(k in name_lower for k in RESTRUCTURE_KEYWORDS):
            # extract `created:` from frontmatter if present
            m = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2})", content, re.MULTILINE)
            d = m.group(1) if m else None
            if not d:
                # fall back to filename date prefix
                m2 = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
                d = m2.group(1) if m2 else None
            if d and in_window(d, start, end):
                # extract title from H1 line if present
                t = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                title = t.group(1) if t else p.name
                events.append(Event(d, "roster", title.strip()[:100], 7, str(p)))
    return events


# ---- output formats -----------------------------------------------------

ROW_LIMIT = 50  # for very busy projects; show top by importance


def render_md(events: list[Event], start: str, end: str, all_events: bool) -> str:
    threshold = 0 if all_events else 4
    filtered = [e for e in events if e.importance >= threshold]
    filtered.sort(key=lambda e: (e.date, -e.importance))

    lines = [
        "## 9.5 Timeline",
        "",
        f"Important events in the window {start} → {end}. "
        f"Generated by `scripts/extract_timeline.py`. "
        f"Showing {'all events' if all_events else f'events with importance ≥{threshold}'}; "
        f"total found: {len(events)}.",
        "",
        "| Date | Event | Type | Importance | Source |",
        "|---|---|---|---|---|",
        f"| {start} | Window start | — | — | — |",
    ]
    for e in filtered[:ROW_LIMIT]:
        bold = "**" if e.importance >= 7 else ""
        lines.append(f"| {bold}{e.date}{bold} | {bold}{e.title}{bold} | {e.type} | {e.importance} | {e.source} |")
    lines.append(f"| {end} | Window end | — | — | — |")

    if not all_events:
        excluded = sum(1 for e in events if e.importance < threshold)
        if excluded:
            lines += ["", f"_{excluded} events with importance <{threshold} excluded — pass `--all` to include._"]

    return "\n".join(lines)


def render_json(events: list[Event], start: str, end: str, all_events: bool) -> str:
    return json.dumps({
        "window": {"start": start, "end": end},
        "events_total": len(events),
        "events_returned": len(events) if all_events else len([e for e in events if e.importance >= 4]),
        "events": [asdict(e) for e in events if all_events or e.importance >= 4],
    }, indent=2)


# ---- main ---------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--coordination", type=Path, default=None,
                    help="Path to the coordination repo or vault root.")
    ap.add_argument("--audit-dir", type=Path, default=None,
                    help="Optional audit output dir to scan snapshots/.")
    ap.add_argument("--window-start", required=True)
    ap.add_argument("--window-end", default=date.today().isoformat())
    ap.add_argument("--format", choices=("md", "json"), default="md")
    ap.add_argument("--all", action="store_true", help="Include events with importance <4")
    args = ap.parse_args(argv[1:])

    if not args.repo.exists():
        print(f"error: repo not found: {args.repo}", file=sys.stderr)
        return 1

    events: list[Event] = []
    events += detect_project_creation(args.repo, args.window_start, args.window_end)
    events += detect_release_tags(args.repo, args.window_start, args.window_end)
    events += detect_adr_creations(args.repo, args.window_start, args.window_end)
    events += detect_convention_changes(args.repo, args.window_start, args.window_end)
    events += detect_incidents(args.repo, args.window_start, args.window_end)
    events += detect_large_features(args.repo, args.window_start, args.window_end)

    # Coordination-side detection (handoffs, audit snapshots)
    if args.coordination:
        events += detect_roster_changes(args.coordination, args.window_start, args.window_end)
    if args.audit_dir:
        events += detect_audit_snapshots(args.audit_dir, args.window_start, args.window_end)

    if args.format == "md":
        print(render_md(events, args.window_start, args.window_end, args.all))
    else:
        print(render_json(events, args.window_start, args.window_end, args.all))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
