#!/usr/bin/env python3
"""
render_short.py — Render the single-page short-form executive summary.

Target audience: someone who'll read for 30 seconds. The full report
(render_report.py) ships alongside for anyone who wants the evidence chain.

Applies addenda overrides like render_report.py does, so the surfaced numbers
reflect the audit's latest understanding (not frozen body values).

Stdlib-only.

Usage:
  python3 render_short.py --snapshot <snapshot.json> --output <out.md|out.html>
                          [--format md|html] [--full-report-path <path>]

If --format is omitted, inferred from the --output extension.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import sys
from pathlib import Path


# Reuse the addenda logic from render_report.py (duplicated here to keep
# render_short.py invocable standalone without a sibling import).

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
    out = json.loads(json.dumps(snapshot))
    for a in (out.get("addenda") or []):
        for path, val in (a.get("revised_values") or {}).items():
            set_path(out, path, val)
    return out


def metric_value(snapshot, dotpath):
    raw = get_path(snapshot, dotpath)
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"]
    return raw


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        if v == 0:
            return "0"
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return s if s else "0"
    return str(v)


def render_md(snap, full_report_path):
    eff = apply_addenda(snap)
    audit_run = eff.get("audit_run") or {}
    verdict = eff.get("verdict") or {}
    opps = (eff.get("ranked_opportunities") or [])[:3]

    project = audit_run.get("project_name", "?")
    date = (audit_run.get("timestamp") or "")[:10]
    pattern = verdict.get("pattern", "?")
    summary = verdict.get("summary", "")
    tax = fmt(metric_value(eff, "metrics.autonomy.intervention_tax"))
    split = fmt(metric_value(eff, "metrics.autonomy.autonomy_split"))
    fidelity = fmt((eff.get("operational_fidelity") or {}).get("score"))

    lines = [
        f"# Multi-agent audit — {project} — {date}",
        "",
        f"**Verdict:** {pattern}",
        f"*{summary}*",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Intervention tax | {tax} |",
        f"| Autonomy split | {split} |",
        f"| Operational fidelity | {fidelity} |",
        "",
        "## Top opportunities",
        "",
    ]
    for i, opp in enumerate(opps, start=1):
        what = opp.get("what", "?")
        why = opp.get("why", "")
        score = opp.get("leverage_ease_score", "?")
        lines.append(f"{i}. **{what}** — {why} *(score {score}/9)*")

    if full_report_path:
        lines += ["", f"Full report: [{full_report_path}]({full_report_path})"]

    # Independence note (1 line)
    indep = audit_run.get("auditor_independence") or {}
    if indep.get("auditor_is_participant"):
        personas = ", ".join(indep.get("participant_personas") or []) or "(unnamed)"
        lines += ["", f"_Auditor-independence note: participant personas `{personas}`. Findings may be softened on Agents/Coordination/Knowledge-capture._"]

    return "\n".join(lines) + "\n"


HTML_STYLES = """
<style>
  * { box-sizing: border-box; }
  body {
    background: #0c0a09; color: #f5f5f4;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    margin: 0; padding: 2rem; line-height: 1.5;
  }
  .wrap { max-width: 700px; margin: 0 auto; }
  h1 { font-style: italic; letter-spacing: -0.01em; margin: 0 0 0.25rem; font-size: 1.3rem; }
  h1 .accent { color: #10b981; }
  .meta { color: #a8a29e; font-size: 0.85rem; margin-bottom: 1.5rem; }
  .verdict {
    background: #1c1917; border: 1px solid #292524; border-radius: 12px;
    padding: 1.25rem; margin-bottom: 1.5rem;
  }
  .verdict .label { color: #a8a29e; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }
  .verdict .pattern { font-weight: 600; color: #10b981; font-size: 1.2rem; margin-top: 0.25rem; }
  .verdict .pattern.warn { color: #f59e0b; }
  .verdict .pattern.bad { color: #f43f5e; }
  .verdict .summary { margin-top: 0.5rem; color: #a8a29e; font-size: 0.9rem; }
  .metrics { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
  .metric { background: #1c1917; border: 1px solid #292524; border-radius: 10px; padding: 1rem; }
  .metric .l { color: #a8a29e; text-transform: uppercase; font-size: 0.65rem; letter-spacing: 0.05em; }
  .metric .v { font-size: 1.5rem; font-weight: 600; margin-top: 0.25rem; }
  h2 { font-size: 1rem; margin: 1.5rem 0 0.5rem; color: #f5f5f4; }
  ol { padding-left: 1.5rem; }
  ol li { margin-bottom: 0.75rem; }
  ol li b { color: #f5f5f4; }
  ol li .why { color: #a8a29e; font-size: 0.9rem; }
  ol li .score { color: #10b981; font-size: 0.8rem; font-weight: 600; }
  a { color: #38bdf8; }
  .footer { margin-top: 2rem; color: #a8a29e; font-size: 0.8rem; }
  .indep {
    margin-top: 1.5rem; padding: 0.75rem 1rem;
    border-left: 3px solid #38bdf8; background: rgba(56, 189, 248, 0.08);
    color: #a8a29e; font-size: 0.85rem;
  }
</style>
"""


def esc(s):
    return html_lib.escape(str(s if s is not None else ""))


def render_html(snap, full_report_path):
    eff = apply_addenda(snap)
    audit_run = eff.get("audit_run") or {}
    verdict = eff.get("verdict") or {}
    opps = (eff.get("ranked_opportunities") or [])[:3]

    project = audit_run.get("project_name", "?")
    date = (audit_run.get("timestamp") or "")[:10]
    pattern = verdict.get("pattern", "?")
    summary = verdict.get("summary", "")
    tax = fmt(metric_value(eff, "metrics.autonomy.intervention_tax"))
    split = fmt(metric_value(eff, "metrics.autonomy.autonomy_split"))
    fidelity = fmt((eff.get("operational_fidelity") or {}).get("score"))

    # Pattern colour-class
    p_lower = (pattern or "").lower()
    p_class = "pattern"
    if "weak" in p_lower and "low-fidelity" in p_lower:
        p_class += " bad"
    elif "low-fidelity" in p_lower or "partially" in p_lower:
        p_class += " warn"

    opp_html = "".join(
        f"<li><b>{esc(o.get('what'))}</b> — <span class=\"why\">{esc(o.get('why'))}</span> "
        f"<span class=\"score\">(score {esc(o.get('leverage_ease_score', '?'))}/9)</span></li>"
        for o in opps
    )

    indep = audit_run.get("auditor_independence") or {}
    indep_html = ""
    if indep.get("auditor_is_participant"):
        personas = ", ".join(indep.get("participant_personas") or [])
        indep_html = (
            f'<div class="indep">Auditor-independence note — participant personas '
            f'<code>{esc(personas)}</code>. Findings on Agents/Coordination/Knowledge-capture may be softened.</div>'
        )

    full_link = (
        f'<div class="footer">Full report: <a href="{esc(full_report_path)}">{esc(full_report_path)}</a></div>'
        if full_report_path else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Multi-agent audit — {esc(project)} — {esc(date)} (short)</title>
{HTML_STYLES}
</head>
<body><div class="wrap">
<h1>Multi-agent audit — <span class="accent">{esc(project)}</span></h1>
<div class="meta">Audit date: <strong>{esc(date)}</strong> · short-form executive summary</div>

<div class="verdict">
  <div class="label">Verdict</div>
  <div class="{p_class}">{esc(pattern)}</div>
  <div class="summary">{esc(summary)}</div>
</div>

<div class="metrics">
  <div class="metric"><div class="l">Intervention tax</div><div class="v">{esc(tax)}</div></div>
  <div class="metric"><div class="l">Autonomy split</div><div class="v">{esc(split)}</div></div>
  <div class="metric"><div class="l">Op. fidelity</div><div class="v">{esc(fidelity)}</div></div>
</div>

<h2>Top opportunities</h2>
<ol>{opp_html}</ol>

{indep_html}
{full_link}
</div></body></html>
"""


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--format", choices=("md", "html"), default=None)
    ap.add_argument("--full-report-path", default=None)
    args = ap.parse_args(argv[1:])

    if not args.snapshot.exists():
        print(f"error: snapshot not found: {args.snapshot}", file=sys.stderr); return 1

    fmt_ = args.format
    if fmt_ is None:
        fmt_ = "html" if args.output.suffix.lower() == ".html" else "md"

    snap = json.loads(args.snapshot.read_text())
    out = render_html(snap, args.full_report_path) if fmt_ == "html" else render_md(snap, args.full_report_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out)
    print(f"wrote {args.output} ({len(out):,} bytes; format={fmt_})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
