#!/usr/bin/env python3
"""
trend_reader.py — Read multi-agent-audit snapshots and emit the §10 Trend section.

Walks a `snapshots/` directory of `*.json` files, sorts by `audit_run.timestamp`,
applies any `addenda[*].revised_values` overrides per snapshot, and computes
deltas on the canonical trend metrics between the two most recent snapshots.

Usage:
  python3 trend_reader.py <snapshots-dir>          # markdown output (default)
  python3 trend_reader.py <snapshots-dir> --json   # JSON output for downstream tools

Read-only. Touches nothing in the audited project.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_VERSIONS_SUPPORTED = {"1.0", "1.1"}

# Canonical metrics to compute deltas on (dot-paths into the snapshot body).
# Order matters for the rendered table.
TREND_METRICS = [
    ("metrics.autonomy.intervention_tax", "Intervention tax", "lower_is_better"),
    ("operational_fidelity.score", "Operational fidelity", "higher_is_better"),
    ("metrics.quality_rework.rework_rate", "Rework rate", "lower_is_better"),
    ("metrics.dora.merge_gate_wait_p50_hours", "Merge-gate wait p50 (h)", "lower_is_better"),
    ("metrics.pr_review.pct_prs_with_zero_reviews", "% PRs zero reviews", "lower_is_better"),
]


def get_path(d: dict, dotpath: str):
    """Traverse a dotted path through a dict; return None if missing."""
    cur = d
    for part in dotpath.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def set_path(d: dict, dotpath: str, value) -> None:
    """Set a value at a dotted path; create intermediate dicts as needed."""
    parts = dotpath.split(".")
    cur = d
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


def apply_addenda(snapshot: dict) -> dict:
    """Return a copy of snapshot with all addenda.revised_values applied in order."""
    out = json.loads(json.dumps(snapshot))  # deep copy
    addenda = out.get("addenda") or []
    for a in addenda:
        for path, val in (a.get("revised_values") or {}).items():
            set_path(out, path, val)
    return out


def extract_metric_value(snapshot: dict, dotpath: str):
    """Pull a numeric value from a metrics-style snapshot entry.

    Snapshot fields shaped like {"value": X, "confidence": "..."} are unwrapped;
    bare values are returned as-is. Returns (value, confidence) or (None, None).
    """
    raw = get_path(snapshot, dotpath)
    if raw is None:
        return None, None
    if isinstance(raw, dict) and "value" in raw:
        return raw.get("value"), raw.get("confidence")
    return raw, None


def fmt_value(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".") if v != 0 else "0"
    return str(v)


def fmt_delta(prev, curr, direction: str) -> tuple[str, str]:
    """Return (delta_text, direction_marker) for a metric pair."""
    if prev is None or curr is None or not isinstance(prev, (int, float)) or not isinstance(curr, (int, float)):
        return "—", "—"
    delta = curr - prev
    if delta == 0:
        return "0", "→ flat"
    sign = "+" if delta > 0 else ""
    delta_text = f"{sign}{delta:.4f}".rstrip("0").rstrip(".")
    if direction == "lower_is_better":
        marker = "↓ better" if delta < 0 else "↑ worse"
    else:
        marker = "↑ better" if delta > 0 else "↓ worse"
    return delta_text, marker


def load_snapshots(snapshots_dir: Path) -> list[dict]:
    """Load all valid snapshots from snapshots_dir, sorted by timestamp."""
    out = []
    for p in sorted(snapshots_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"warning: skipping {p.name} — invalid JSON ({e})", file=sys.stderr)
            continue
        sv = data.get("schema_version")
        if sv not in SCHEMA_VERSIONS_SUPPORTED:
            print(f"warning: skipping {p.name} — unsupported schema v{sv}", file=sys.stderr)
            continue
        ts = (data.get("audit_run") or {}).get("timestamp")
        if not ts:
            print(f"warning: skipping {p.name} — no audit_run.timestamp", file=sys.stderr)
            continue
        out.append((ts, p, data))
    out.sort(key=lambda t: t[0])
    return [(p, d) for (_, p, d) in out]


def render_markdown(snapshots: list, project_name: str) -> str:
    if len(snapshots) < 2:
        return (
            "## 10. Trend\n\n"
            f"_Only one snapshot exists ({len(snapshots)}). "
            "Trend data appears after the second audit._\n"
        )

    prev_path, prev = snapshots[-2]
    curr_path, curr = snapshots[-1]
    prev_eff = apply_addenda(prev)
    curr_eff = apply_addenda(curr)

    prev_ts = (prev_eff.get("audit_run") or {}).get("timestamp", "?")
    curr_ts = (curr_eff.get("audit_run") or {}).get("timestamp", "?")

    lines = [
        "## 10. Trend",
        "",
        f"Compared to {prev_ts} (`{prev_path.name}`):",
        "",
        "| Metric | Previous | Current | Δ | Direction |",
        "|---|---|---|---|---|",
    ]

    for dotpath, label, direction in TREND_METRICS:
        pv, _ = extract_metric_value(prev_eff, dotpath)
        cv, _ = extract_metric_value(curr_eff, dotpath)
        delta_text, marker = fmt_delta(pv, cv, direction)
        lines.append(f"| {label} | {fmt_value(pv)} | {fmt_value(cv)} | {delta_text} | {marker} |")

    # Window-mismatch note if window lengths differ significantly
    prev_days = ((prev_eff.get("audit_run") or {}).get("time_window") or {}).get("days")
    curr_days = ((curr_eff.get("audit_run") or {}).get("time_window") or {}).get("days")
    if prev_days and curr_days and abs(prev_days - curr_days) > max(prev_days, curr_days) * 0.5:
        lines += [
            "",
            f"*Note:* time-window sizes differ significantly (previous: {prev_days}d, current: {curr_days}d). "
            "Rate metrics compared directly; count metrics may need per-week normalization for fair comparison.",
        ]

    # Addenda awareness
    prev_addenda = prev.get("addenda") or []
    curr_addenda = curr.get("addenda") or []
    if prev_addenda or curr_addenda:
        lines += [
            "",
            "*Addenda applied:* "
            + ", ".join([f"previous {len(prev_addenda)}", f"current {len(curr_addenda)}"])
            + ". Trend math uses revised values from each snapshot's `addenda[*].revised_values`; original body values remain for provenance.",
        ]

    lines += [
        "",
        "Headline trend: _{{summarize the dominant direction in one sentence — auditor fills}}_",
    ]
    return "\n".join(lines)


def render_json(snapshots: list) -> str:
    if len(snapshots) < 2:
        return json.dumps({"trend_available": False, "snapshot_count": len(snapshots)}, indent=2)

    prev_path, prev = snapshots[-2]
    curr_path, curr = snapshots[-1]
    prev_eff = apply_addenda(prev)
    curr_eff = apply_addenda(curr)

    rows = []
    for dotpath, label, direction in TREND_METRICS:
        pv, _ = extract_metric_value(prev_eff, dotpath)
        cv, _ = extract_metric_value(curr_eff, dotpath)
        rows.append({
            "metric": label,
            "dotpath": dotpath,
            "direction": direction,
            "previous": pv,
            "current": cv,
            "delta": (cv - pv) if isinstance(pv, (int, float)) and isinstance(cv, (int, float)) else None,
        })

    return json.dumps({
        "trend_available": True,
        "previous": {
            "path": str(prev_path),
            "timestamp": (prev_eff.get("audit_run") or {}).get("timestamp"),
            "window_days": ((prev_eff.get("audit_run") or {}).get("time_window") or {}).get("days"),
            "addenda_applied": len(prev.get("addenda") or []),
        },
        "current": {
            "path": str(curr_path),
            "timestamp": (curr_eff.get("audit_run") or {}).get("timestamp"),
            "window_days": ((curr_eff.get("audit_run") or {}).get("time_window") or {}).get("days"),
            "addenda_applied": len(curr.get("addenda") or []),
        },
        "rows": rows,
    }, indent=2)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 1
    out_json = "--json" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print("error: missing <snapshots-dir>", file=sys.stderr)
        return 1

    snap_dir = Path(args[0])
    if not snap_dir.exists() or not snap_dir.is_dir():
        print(f"error: snapshots directory not found: {snap_dir}", file=sys.stderr)
        return 1

    snapshots = load_snapshots(snap_dir)
    project_name = "?"
    if snapshots:
        project_name = (snapshots[-1][1].get("audit_run") or {}).get("project_name", "?")

    print(render_json(snapshots) if out_json else render_markdown(snapshots, project_name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
