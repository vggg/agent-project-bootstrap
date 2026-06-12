#!/usr/bin/env python3
"""
render_report.py — Render the HTML dashboard from a snapshot JSON + the
shipped template.

Reads a multi-agent-audit snapshot (v1.0 or v1.1), applies any
`addenda[*].revised_values`, generates HTML fragments for the template's
`<!-- INSERT:X -->` markers + simple `{{X}}` placeholders, and writes the
filled HTML to disk.

Stdlib-only. The renderer's job is data → HTML; no charting math runs here
(that's Chart.js client-side via the CDN reference in the template).

Usage:
  python3 render_report.py \\
    --snapshot <snapshot.json> \\
    [--timeline-json <timeline.json>] \\
    [--template <template.html>] \\
    --output <output.html>

If --template is omitted, the script uses
`<skill-dir>/assets/report-template.html` (auto-detected from the script's
location).

Read-only on the snapshot/template. Writes only --output.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import sys
from datetime import datetime
from pathlib import Path


# --- helpers (reused from trend_reader.py with minor adaptations) ---

def get_path(d, dotpath, default=None):
    cur = d
    for part in dotpath.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def set_path(d, dotpath, value):
    parts = dotpath.split(".")
    cur = d
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


def apply_addenda(snapshot):
    out = json.loads(json.dumps(snapshot))  # deep copy
    for a in (out.get("addenda") or []):
        for path, val in (a.get("revised_values") or {}).items():
            set_path(out, path, val)
    return out


def metric_value(snapshot, dotpath):
    raw = get_path(snapshot, dotpath)
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"]
    return raw


def esc(s):
    if s is None:
        return ""
    return html_lib.escape(str(s))


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        if v == 0:
            return "0"
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return s if s else "0"
    return str(v)


# --- fragment builders ---

CONF_CLASS = {
    "measured": "measured",
    "inferred": "inferred",
    "not measurable": "not-measurable",
}


def render_drift_rows(snap):
    rows = []
    for d in (snap.get("drift_scorecard") or []):
        conf = (d.get("confidence") or "not measurable").lower()
        conf_class = CONF_CLASS.get(conf, "not-measurable")
        rows.append(
            "<tr>"
            f"<td>{esc(d.get('dimension'))}</td>"
            f"<td>{esc(d.get('intended'))}</td>"
            f"<td>{esc(d.get('actual'))}</td>"
            f"<td>{esc(d.get('gap'))}</td>"
            f"<td><span class=\"conf-{conf_class}\">{esc(conf)}</span></td>"
            "</tr>"
        )
    return "\n".join(rows) if rows else '<tr><td colspan="5"><em>No drift scorecard in snapshot.</em></td></tr>'


def render_agent_rows(snap):
    rows = []
    for a in (snap.get("agent_inventory") or []):
        m = a.get("metrics") or {}
        rows.append(
            "<tr>"
            f"<td>{esc(a.get('actor'))}</td>"
            f"<td>{esc(a.get('class'))}</td>"
            f"<td>{esc(a.get('declared'))}</td>"
            f"<td>{esc(a.get('observed'))}</td>"
            f"<td class=\"num\">{esc(m.get('commits_raw', m.get('commits', 0)))}</td>"
            f"<td class=\"num\">{esc(m.get('prs_opened', 0))}</td>"
            f"<td class=\"num\">{esc(m.get('prs_reviewed', m.get('reviews', 0)))}</td>"
            f"<td class=\"num\">{esc(m.get('handoffs_sent', 0))}</td>"
            "</tr>"
        )
    return "\n".join(rows) if rows else '<tr><td colspan="8"><em>No agent inventory in snapshot.</em></td></tr>'


def render_opportunity_rows(snap):
    items = []
    for o in (snap.get("ranked_opportunities") or []):
        items.append(
            "<li>"
            f"<strong>{esc(o.get('what'))}</strong> — {esc(o.get('why'))}"
            f"<div style=\"color: var(--muted); font-size: 0.85rem;\">"
            f"How: {esc(o.get('how'))} &middot; Score: {esc(o.get('leverage_ease_score', '?'))}/9"
            "</div>"
            "</li>"
        )
    return "\n".join(items) if items else '<li><em>No ranked opportunities in snapshot.</em></li>'


def render_per_persona_scorecards(snap):
    """Pull per-persona inventory and render a small card per persona.

    Skipped (returns "") when there are <3 personas in the inventory.
    """
    inv = snap.get("agent_inventory") or []
    if len(inv) < 3:
        return ""
    cards = ['<h2>Per-persona scorecards</h2>', '<div class="grid three">']
    for a in inv[:12]:  # cap visual density
        m = a.get("metrics") or {}
        actor = esc(a.get("actor", "?"))
        klass = esc(a.get("class", "?"))
        declared = esc(a.get("declared", "?"))
        observed = esc(a.get("observed", "?"))
        notes = esc(a.get("notes", "") or "")
        # Top metrics
        items = []
        for k, label in [("commits_raw", "Commits"), ("prs_opened", "PRs opened"),
                         ("prs_reviewed", "PRs reviewed"), ("issues_claimed", "Issues claimed"),
                         ("handoffs_sent", "Handoffs sent"), ("handoffs_received", "Handoffs received"),
                         ("issues_filed_uat", "UAT issues filed")]:
            if k in m and m[k] not in (None, 0, "0"):
                items.append(f"<li>{label}: <strong>{esc(m[k])}</strong></li>")
        items_html = "<ul style='margin: 0.5rem 0; padding-left: 1.2rem; font-size: 0.85rem;'>" + "".join(items) + "</ul>"
        cards.append(
            "<div class=\"card\">"
            f"<h3>{actor}</h3>"
            f"<div class=\"sub\">{klass} &middot; declared {declared} &middot; observed {observed}</div>"
            f"{items_html}"
            + (f"<div class=\"sub\" style=\"margin-top: 0.5rem;\">{notes}</div>" if notes else "")
            + "</div>"
        )
    cards.append("</div>")
    return "\n".join(cards)


def render_caveat_rows(snap):
    methodology = (snap.get("audit_run") or {}).get("methodology_notes")
    items = []
    if methodology:
        items.append(f"<li>{esc(methodology)}</li>")
    # Surface all not-measurable values from metrics
    metrics = snap.get("metrics") or {}
    for cat, cat_data in metrics.items():
        if not isinstance(cat_data, dict):
            continue
        for k, v in cat_data.items():
            if isinstance(v, dict) and v.get("confidence") == "not measurable":
                note = v.get("note", "")
                items.append(f"<li><code>{esc(cat)}.{esc(k)}</code> — not measurable. {esc(note)}</li>")
    return "\n".join(items) if items else "<li><em>No caveats logged in snapshot.</em></li>"


def render_trend_section(snap, prev_snap=None):
    if not prev_snap:
        return '<div class="sub">Only one snapshot exists — trend data appears after the second audit.</div>'
    # Minimal in-template trend rendering (full computation in trend_reader.py)
    prev_eff = apply_addenda(prev_snap)
    curr_eff = apply_addenda(snap)
    trend_metrics = [
        ("metrics.autonomy.intervention_tax", "Intervention tax", "lower_is_better"),
        ("operational_fidelity.score", "Operational fidelity", "higher_is_better"),
        ("metrics.quality_rework.rework_rate", "Rework rate", "lower_is_better"),
        ("metrics.pr_review.pct_prs_with_zero_reviews", "% PRs zero reviews", "lower_is_better"),
    ]
    rows = []
    for dp, label, direction in trend_metrics:
        p = metric_value(prev_eff, dp); c = metric_value(curr_eff, dp)
        delta = (c - p) if isinstance(p, (int, float)) and isinstance(c, (int, float)) else None
        marker = ""
        if delta is not None and delta != 0:
            if direction == "lower_is_better":
                marker = "↓ better" if delta < 0 else "↑ worse"
            else:
                marker = "↑ better" if delta > 0 else "↓ worse"
        rows.append(
            f"<tr><td>{esc(label)}</td>"
            f"<td>{esc(fmt(p))}</td>"
            f"<td>{esc(fmt(c))}</td>"
            f"<td>{esc(fmt(delta) if delta is not None else '—')}</td>"
            f"<td>{esc(marker or '—')}</td></tr>"
        )
    prev_ts = (prev_eff.get('audit_run') or {}).get('timestamp', '?')
    return (
        f'<table><thead><tr><th>Metric</th><th>Previous ({esc(prev_ts)})</th>'
        '<th>Current</th><th>Δ</th><th>Direction</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def render_addenda_section(snap):
    addenda = snap.get("addenda") or []
    if not addenda:
        return ""
    rows = []
    for a in addenda:
        affects = ", ".join(a.get("affects", []))
        rows.append(
            "<tr>"
            f"<td>{esc(a.get('id'))}</td>"
            f"<td>{esc((a.get('created') or '')[:10])}</td>"
            f"<td>{esc(a.get('title'))}</td>"
            f"<td><code>{esc(affects)}</code></td>"
            f"<td><a href=\"{esc(a.get('path'))}\">{esc(a.get('path'))}</a></td>"
            "</tr>"
        )
    return (
        '<h2>Addenda</h2>'
        '<div class="card">'
        '<table><thead><tr><th>ID</th><th>Created</th><th>Title</th><th>Affects</th><th>Path</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
        '</div>'
    )


def render_false_win_callout(snap):
    autonomy = metric_value(snap, "metrics.autonomy.autonomy_split")
    tax = metric_value(snap, "metrics.autonomy.intervention_tax")
    if isinstance(autonomy, (int, float)) and isinstance(tax, (int, float)) and autonomy > 0.5 and tax > 1.0:
        return (
            '<div class="callout bad">'
            f'<strong>False-win callout.</strong> Autonomy split {fmt(autonomy)} with intervention tax {fmt(tax)} — '
            'the multi-agent setup is doing MORE work than a single-agent or pure-human flow would have. '
            'Consider whether the overhead is earning its keep.'
            '</div>'
        )
    return ""


def render_independence_callout(snap):
    indep = (snap.get("audit_run") or {}).get("auditor_independence") or {}
    if indep.get("auditor_is_participant"):
        personas = ", ".join(indep.get("participant_personas") or []) or "(unnamed)"
        rationale = indep.get("rationale", "")
        return (
            '<div class="callout info">'
            f'<strong>Auditor-independence note.</strong> The auditor is a participant in the audited project '
            f'(personas: <code>{esc(personas)}</code>). '
            f'{esc(rationale)} '
            'Findings on Agents / Coordination / Knowledge-capture dimensions may be softened; calibrate confidence accordingly.'
            '</div>'
        )
    return ""


# --- timeline SVG ---

TIMELINE_TYPE_COLORS = {
    "release": "#10b981",
    "feature": "#10b981",
    "adr": "#38bdf8",
    "adr_accepted": "#38bdf8",
    "decision": "#38bdf8",
    "roster": "#f59e0b",
    "convention": "#a8a29e",
    "incident": "#f43f5e",
    "audit": "#a855f7",
    "start": "#a8a29e",
    "end": "#a8a29e",
}


def render_timeline_svg(events, window_start, window_end, width=1100, height=160):
    if not events:
        return '<div class="sub">No timeline events found.</div>'
    try:
        start_d = datetime.fromisoformat(window_start)
        end_d = datetime.fromisoformat(window_end)
    except ValueError:
        return '<div class="sub">Invalid timeline window.</div>'
    total_days = max((end_d - start_d).days, 1)

    margin_l, margin_r = 60, 60
    plot_w = width - margin_l - margin_r
    y_axis = 100

    def x_for(d_str):
        try:
            d = datetime.fromisoformat(d_str)
        except ValueError:
            return margin_l
        days_in = (d - start_d).days
        return margin_l + max(0, min(1, days_in / total_days)) * plot_w

    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<line x1="{margin_l}" y1="{y_axis}" x2="{width - margin_r}" y2="{y_axis}" stroke="#a8a29e" stroke-width="1"/>',
    ]
    # Week ticks
    for d_offset in range(0, total_days + 1, 7):
        x = margin_l + (d_offset / total_days) * plot_w
        parts.append(f'<line x1="{x}" y1="{y_axis - 4}" x2="{x}" y2="{y_axis + 4}" stroke="#292524"/>')
    # Window bounds
    parts.append(f'<text x="{margin_l}" y="{y_axis + 25}" fill="#a8a29e" font-size="10" text-anchor="start">{esc(window_start)}</text>')
    parts.append(f'<text x="{width - margin_r}" y="{y_axis + 25}" fill="#a8a29e" font-size="10" text-anchor="end">{esc(window_end)}</text>')

    # Sort events by date for layout
    sorted_events = sorted(events, key=lambda e: (e.get("date", ""), -e.get("importance", 0)))

    # Label collision avoidance: alternate above/below for high-importance items
    used_high_xpositions = []

    for e in sorted_events:
        date_s = e.get("date") or ""
        x = x_for(date_s)
        importance = int(e.get("importance") or 0)
        type_ = e.get("type") or "convention"
        color = TIMELINE_TYPE_COLORS.get(type_, "#a8a29e")
        r = 3 + min(5, importance // 2)
        title = e.get("title", "")
        # Marker
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y_axis}" r="{r}" fill="{color}" opacity="0.9" stroke="#0c0a09" stroke-width="0.5">'
            f'<title>{esc(date_s)}: {esc(title)} ({esc(type_)}, importance {importance})</title>'
            '</circle>'
        )
        # Label for high-importance
        if importance >= 7 and title:
            # Stagger label height if multiple high-importance are within 80px of each other
            offset_y = -16
            for prev_x in used_high_xpositions[-3:]:
                if abs(prev_x - x) < 80:
                    offset_y -= 12
            used_high_xpositions.append(x)
            label = title[:40] + ("…" if len(title) > 40 else "")
            parts.append(
                f'<text x="{x:.1f}" y="{y_axis + offset_y}" fill="#f5f5f4" font-size="10" text-anchor="middle">{esc(label)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


# --- chart-data JSON for the script block ---

def build_chart_data(snap, timeline_events):
    """Produce the JSON object the in-template script reads as `data`."""
    inv = snap.get("agent_inventory") or []
    autonomy_split = metric_value(snap, "metrics.autonomy.autonomy_split") or 0
    hybrid_initiated = metric_value(snap, "metrics.autonomy.hybrid_initiated_tasks") or 0
    autonomous_initiated = metric_value(snap, "metrics.autonomy.autonomous_initiated_tasks") or 0
    human_tasks = max(0, (metric_value(snap, "metrics.throughput.commits_total") or 0) - hybrid_initiated - autonomous_initiated)

    persona_labels = [a.get("actor") or "?" for a in inv if a.get("actor")]
    persona_commits = [(a.get("metrics") or {}).get("commits_raw") or (a.get("metrics") or {}).get("commits") or 0 for a in inv]
    persona_reviews = [(a.get("metrics") or {}).get("prs_reviewed") or (a.get("metrics") or {}).get("reviews") or 0 for a in inv]
    persona_handoffs = [(a.get("metrics") or {}).get("handoffs_sent") or 0 for a in inv]

    # Score radar (5 of the 7 axes — exclude n/a)
    scores = snap.get("scores") or {}
    axis_order = [("throughput", "Throughput"), ("autonomy_low_tax", "Autonomy"),
                  ("coordination", "Coordination"), ("quality_rework", "Quality"),
                  ("guardrail_integrity", "Guardrail"), ("knowledge_capture", "Knowledge"),
                  ("operational_fidelity", "Op. Fidelity")]
    radar_labels, radar_values = [], []
    for k, label in axis_order:
        score = (scores.get(k) or {}).get("score")
        if isinstance(score, (int, float)):
            radar_labels.append(label)
            radar_values.append(score)
        elif score == "n/a":
            radar_labels.append(label + " (n/a)")
            radar_values.append(0)

    return {
        "autonomy": {
            "autonomous": int(autonomous_initiated),
            "hybrid": int(hybrid_initiated),
            "human": int(human_tasks),
        },
        "personas": {
            "labels": persona_labels,
            "commits": persona_commits,
            "reviews": persona_reviews,
            "handoffs": persona_handoffs,
        },
        "throughput": {
            # Per-week aggregation requires raw data; render a flat single-bar
            # if we don't have weekly buckets. v1.4 candidate: weekly histogram.
            "weeks": [],
            "commits": [],
            "prs": [],
        },
        "radar": {
            "labels": radar_labels,
            "scores": radar_values,
        },
        "timeline_events": timeline_events or [],
    }


# --- top-level placeholder substitution ---

def fill_placeholders(template, snap, timeline_events):
    eff = apply_addenda(snap)
    audit_run = eff.get("audit_run") or {}
    indep = audit_run.get("auditor_independence") or {}

    placeholders = {
        "{{PROJECT_NAME}}": esc(audit_run.get("project_name", "?")),
        "{{AUDIT_DATE}}": esc((audit_run.get("timestamp") or "")[:10]),
        "{{WINDOW_START}}": esc((audit_run.get("time_window") or {}).get("start", "?")),
        "{{WINDOW_END}}": esc((audit_run.get("time_window") or {}).get("end", "?")),
        "{{WINDOW_DAYS}}": esc((audit_run.get("time_window") or {}).get("days", "?")),
        "{{SKILL_VERSION}}": esc(audit_run.get("auditor", {}).get("skill_version", "?")),
        "{{VERDICT_PATTERN}}": esc((eff.get("verdict") or {}).get("pattern", "?")),
        "{{VERDICT_SUMMARY}}": esc((eff.get("verdict") or {}).get("summary", "")),
        "{{INTERVENTION_TAX}}": esc(fmt(metric_value(eff, "metrics.autonomy.intervention_tax"))),
        "{{AUTONOMY_SPLIT}}": esc(fmt(metric_value(eff, "metrics.autonomy.autonomy_split"))),
        "{{OPERATIONAL_FIDELITY}}": esc(fmt((eff.get("operational_fidelity") or {}).get("score"))),
        "{{HUMAN_INTERVENTIONS}}": esc(metric_value(eff, "metrics.autonomy.human_intervention_events") or "n/a"),
        "{{AUTONOMOUS_TASKS}}": esc(metric_value(eff, "metrics.autonomy.autonomous_initiated_tasks") or 0),
        "{{LEAD_TIME_P50}}": esc(fmt(metric_value(eff, "metrics.dora.lead_time_p50_days"))),
        "{{LEAD_TIME_P90}}": esc(fmt(metric_value(eff, "metrics.dora.lead_time_pr_p90_days") or metric_value(eff, "metrics.throughput.cycle_time_pr_p90_hours"))),
        "{{FIDELITY_NUMERATOR}}": esc((eff.get("operational_fidelity") or {}).get("numerator", "?")),
        "{{FIDELITY_DENOMINATOR}}": esc((eff.get("operational_fidelity") or {}).get("denominator", "?")),
        "{{LAYOUT_FAMILY}}": esc(audit_run.get("layout_family", "?")),
        "{{BACKLOG_SOURCE}}": esc(audit_run.get("backlog_source", "?")),
        "{{COORDINATION_SUBSTRATE}}": esc(audit_run.get("coordination_substrate", "?")),
        "{{N_DECLARED_ACTORS}}": esc(sum(1 for a in (eff.get("agent_inventory") or []) if a.get("declared"))),
        "{{SOURCE_DOCS}}": esc(audit_run.get("source_docs", "see methodology")),
        "{{SOURCES}}": esc(audit_run.get("methodology_notes", "—")),
        "{{SAMPLING}}": esc(audit_run.get("sampling", "—")),
        "{{IDENTITY_RULES}}": esc(audit_run.get("identity_rules", "multi-substrate (v1.3+)")),
        "{{AUDITOR_IS_PARTICIPANT}}": "true" if indep.get("auditor_is_participant") else "false",
        "{{AUDITOR_PARTICIPATION_NOTE}}": (
            f" — {esc(', '.join(indep.get('participant_personas') or []))}"
            if indep.get("auditor_is_participant") else ""
        ),
        "{{N_MEASURED}}": "—",  # auditor fills via methodology
        "{{N_INFERRED}}": "—",
        "{{N_NOT_MEASURABLE}}": "—",
        "{{AUDIT_DATA_JSON}}": json.dumps(build_chart_data(eff, timeline_events)),
    }
    out = template
    for k, v in placeholders.items():
        out = out.replace(k, str(v))
    return out


def fill_markers(template, snap, timeline_events):
    eff = apply_addenda(snap)
    audit_run = eff.get("audit_run") or {}
    window_start = (audit_run.get("time_window") or {}).get("start", "")
    window_end = (audit_run.get("time_window") or {}).get("end", "")

    markers = {
        "<!-- INSERT:FALSE_WIN_CALLOUT -->": render_false_win_callout(eff),
        "<!-- INSERT:INDEPENDENCE_CALLOUT -->": render_independence_callout(eff),
        "<!-- INSERT:TIMELINE_SVG -->": render_timeline_svg(timeline_events or [], window_start, window_end),
        "<!-- INSERT:DRIFT_ROWS -->": render_drift_rows(eff),
        "<!-- INSERT:AGENT_ROWS -->": render_agent_rows(eff),
        "<!-- INSERT:OPPORTUNITY_ROWS -->": render_opportunity_rows(eff),
        "<!-- INSERT:PER_PERSONA_SCORECARDS -->": render_per_persona_scorecards(eff),
        "<!-- INSERT:TREND_SECTION -->": render_trend_section(eff),
        "<!-- INSERT:ADDENDA_SECTION -->": render_addenda_section(eff),
        "<!-- INSERT:CAVEAT_ROWS -->": render_caveat_rows(eff),
    }
    out = template
    for k, v in markers.items():
        out = out.replace(k, v)
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--timeline-json", type=Path, default=None,
                    help="Optional timeline JSON from extract_timeline.py")
    ap.add_argument("--template", type=Path, default=None,
                    help="HTML template path. Defaults to <skill>/assets/report-template.html.")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args(argv[1:])

    if not args.snapshot.exists():
        print(f"error: snapshot not found: {args.snapshot}", file=sys.stderr); return 1

    template_path = args.template
    if template_path is None:
        # Auto-detect: <script-parent>/assets/report-template.html
        script_path = Path(__file__).resolve()
        template_path = script_path.parent.parent / "assets" / "report-template.html"

    if not template_path.exists():
        print(f"error: template not found: {template_path}", file=sys.stderr); return 1

    template = template_path.read_text()
    snap = json.loads(args.snapshot.read_text())

    timeline_events = []
    if args.timeline_json and args.timeline_json.exists():
        try:
            tj = json.loads(args.timeline_json.read_text())
            timeline_events = tj.get("events", []) if isinstance(tj, dict) else (tj if isinstance(tj, list) else [])
        except json.JSONDecodeError:
            print(f"warning: could not parse timeline JSON {args.timeline_json}", file=sys.stderr)

    # Replace markers first (they can contain {{X}} patterns that should NOT be substituted)
    # Actually order doesn't really matter here since the marker content doesn't include {{X}}.
    out = fill_markers(template, snap, timeline_events)
    out = fill_placeholders(out, snap, timeline_events)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out)
    print(f"wrote {args.output} ({len(out):,} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
