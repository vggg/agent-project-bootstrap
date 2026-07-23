#!/usr/bin/env python3
"""
test_ingest_otel.py — checks for the telemetry-mode scripts
(scripts/ingest_otel.py + scripts/merge_telemetry.py) against the
hand-crafted fixtures in tests/fixtures/.

Covers:
  1. OTLP-JSON ingestion (2 Claude Code sessions: spans + log events,
     span/event dedupe by tool_use_id / request_id, token+cost totals,
     user-prompt counting without double counting interaction spans,
     human-turns-per-task from workflow.run_id).
  2. Flat JSONL ingestion (Logfire-style rows + a Phoenix-style flattened
     row; trace_id session fallback => `inferred` session count).
  3. The honesty rule: absent attributes come back `not measurable` with
     the missing attribute named — never an estimated number; partially
     present attributes come back `inferred` with a coverage note.
  4. merge_telemetry.py: additive merge (git-derived values untouched),
     `otel:<file>` source tags, in-place-overwrite refusal, markdown table.

Run:  python3 tests/test_ingest_otel.py
Stdlib only. Exit code 0 iff all checks pass.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES = TESTS_DIR / "fixtures"

sys.path.insert(0, str(SCRIPTS_DIR))
import ingest_otel  # noqa: E402
import merge_telemetry  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        print(f"  ✓ {name}")
        PASS += 1
    else:
        print(f"  ✗ {name}  {detail}")
        FAIL += 1


def ingest(paths: list[Path]) -> dict:
    records, reports = [], []
    for p in paths:
        recs, rep = ingest_otel.load_file(p)
        records.extend(recs)
        reports.append(rep)
    return ingest_otel.compute_metrics(records, reports)


def approx(a, b, tol=1e-6) -> bool:
    return isinstance(a, (int, float)) and abs(a - b) <= tol


OTLP = FIXTURES / "otlp_two_sessions.json"
FLAT = FIXTURES / "flat_spans.jsonl"
MISSING = FIXTURES / "missing_attrs.jsonl"


def test_otlp_fixture():
    print("--- OTLP-JSON fixture (2 Claude Code sessions) ---")
    m = ingest([OTLP])
    rep = m["ingest"]["files"][0]
    check("format detected otlp-json", rep["format"] == "otlp-json",
          f"got {rep['format']}")
    check("8 spans + 7 events parsed",
          rep["spans"] == 8 and rep["events"] == 7,
          f"got spans={rep['spans']} events={rep['events']}")
    check("no unparseable rows", rep["unparseable"] == 0)
    check("logs stream detected", rep["has_logs_stream"] is True)

    agg = m["aggregate"]
    sc = agg["session_count"]
    check("session_count == 2, measured",
          sc["value"] == 2 and sc["confidence"] == "measured", str(sc))

    sessions = {s["session_id"]: s for s in m["sessions"]}
    check("session ids sess-a / sess-b",
          set(sessions) == {"sess-a", "sess-b"}, str(set(sessions)))
    a, b = sessions.get("sess-a", {}), sessions.get("sess-b", {})
    check("sess-a human_turns == 2 (user_prompt events, interaction spans "
          "not double counted)", a.get("human_turns") == 2,
          str(a.get("human_turns")))
    check("sess-b human_turns == 1", b.get("human_turns") == 1)
    check("sess-a tool_calls == 3 (tool_result event deduped by "
          "tool_use_id)", a.get("tool_calls") == 3,
          str(a.get("tool_calls")))
    check("sess-a tool_errors == 1", a.get("tool_errors") == 1)
    check("sess-a llm_calls == 2 (api_request events merged by request_id)",
          a.get("llm_calls") == 2, str(a.get("llm_calls")))
    check("sess-b llm_calls == 1 (event-only LLM call counted)",
          b.get("llm_calls") == 1, str(b.get("llm_calls")))
    check("sess-a input_tokens == 2000", a.get("input_tokens") == 2000,
          str(a.get("input_tokens")))
    check("sess-a cost_usd == 0.02 (cost from api_request events)",
          approx(a.get("cost_usd"), 0.02), str(a.get("cost_usd")))
    check("sess-a duration 300s", approx(a.get("duration_s"), 300.0),
          str(a.get("duration_s")))
    check("sess-b duration 13s", approx(b.get("duration_s"), 13.0),
          str(b.get("duration_s")))
    check("sess-a tasks == [wf_1]", a.get("tasks") == ["wf_1"],
          str(a.get("tasks")))

    check("tool_calls_total == 4 measured",
          agg["tool_calls_total"]["value"] == 4
          and agg["tool_calls_total"]["confidence"] == "measured")
    check("tool_error_rate == 0.25",
          approx(agg["tool_error_rate"]["value"], 0.25),
          str(agg["tool_error_rate"]))
    check("tool_calls_by_name Bash=2 Edit=1 Read=1",
          agg["tool_calls_by_name"]["value"] ==
          {"Bash": 2, "Edit": 1, "Read": 1},
          str(agg["tool_calls_by_name"]["value"]))
    check("llm_calls_total == 3", agg["llm_calls_total"]["value"] == 3)
    check("input_tokens_total == 2500 measured",
          agg["input_tokens_total"]["value"] == 2500
          and agg["input_tokens_total"]["confidence"] == "measured",
          str(agg["input_tokens_total"]))
    check("output_tokens_total == 600 measured",
          agg["output_tokens_total"]["value"] == 600)
    check("cache_read_tokens_total == 6000 measured",
          agg["cache_read_tokens_total"]["value"] == 6000
          and agg["cache_read_tokens_total"]["confidence"] == "measured",
          str(agg["cache_read_tokens_total"]))
    check("cache_creation_tokens_total == 50 (event fills span gap)",
          agg["cache_creation_tokens_total"]["value"] == 50,
          str(agg["cache_creation_tokens_total"]))
    check("cost_usd_total == 0.025 measured (micros + usd attrs combined)",
          approx(agg["cost_usd_total"]["value"], 0.025)
          and agg["cost_usd_total"]["confidence"] == "measured",
          str(agg["cost_usd_total"]))
    check("human_turns_total == 3 measured",
          agg["human_turns_total"]["value"] == 3
          and agg["human_turns_total"]["confidence"] == "measured",
          str(agg["human_turns_total"]))
    check("human_turns_per_session_mean == 1.5",
          approx(agg["human_turns_per_session_mean"]["value"], 1.5))
    hpt = agg["human_turns_per_task"]
    check("human_turns_per_task == 1.5 measured (workflow.run_id present)",
          approx(hpt["value"], 1.5) and hpt["confidence"] == "measured",
          str(hpt))
    check("per-task note admits completion status is not encoded",
          "not per completed task" in (hpt.get("note") or ""))
    check("session_duration_p50_s == 156.5",
          approx(agg["session_duration_p50_s"]["value"], 156.5),
          str(agg["session_duration_p50_s"]))
    check("session_duration_total_s == 313",
          approx(agg["session_duration_total_s"]["value"], 313.0))
    check("distinct_models sorted",
          agg["distinct_models"]["value"] ==
          ["claude-haiku-4-5", "claude-sonnet-4-5"],
          str(agg["distinct_models"]["value"]))
    check("measured metrics carry the source file",
          agg["input_tokens_total"].get("source") ==
          ["otlp_two_sessions.json"],
          str(agg["input_tokens_total"].get("source")))
    return m


def test_flat_fixture():
    print("--- flat JSONL fixture (Logfire/Phoenix style rows) ---")
    m = ingest([FLAT])
    rep = m["ingest"]["files"][0]
    check("format detected jsonl", rep["format"] == "jsonl",
          f"got {rep['format']}")
    agg = m["aggregate"]
    sc = agg["session_count"]
    check("session_count == 1, INFERRED (trace_id fallback, no "
          "session.id)", sc["value"] == 1 and sc["confidence"] == "inferred",
          str(sc))
    s = m["sessions"][0]
    check("identity method is trace_id fallback",
          s["identity_method"] == "trace_id fallback",
          s["identity_method"])
    check("duration 600s from ISO timestamps",
          approx(s["duration_s"], 600.0), str(s["duration_s"]))
    check("human_turns == 1 (gen_ai.user.message event)",
          s["human_turns"] == 1, str(s["human_turns"]))
    check("Phoenix-style flattened row parsed as a tool call "
          "(span_kind=TOOL, attributes.tool.name, context.trace_id)",
          s["tool_calls"] == 1 and
          agg["tool_calls_by_name"]["value"] == {"run_sql": 1},
          f"tool_calls={s['tool_calls']} "
          f"by_name={agg['tool_calls_by_name']['value']}")
    check("status_code ERROR counted as tool error",
          s["tool_errors"] == 1 and
          approx(agg["tool_error_rate"]["value"], 1.0))
    check("gen_ai.usage.* tokens measured (900/250)",
          agg["input_tokens_total"]["value"] == 900
          and agg["output_tokens_total"]["value"] == 250,
          str(agg["input_tokens_total"]))
    cost = agg["cost_usd_total"]
    check("cost NOT MEASURABLE (attribute absent) — never estimated "
          "from tokens", cost["value"] == "not measurable"
          and cost["confidence"] == "not measurable"
          and "attribute absent" in cost["note"], str(cost))
    hpt = agg["human_turns_per_task"]
    check("human_turns_per_task NOT MEASURABLE (no task-boundary attrs)",
          hpt["confidence"] == "not measurable"
          and "task-boundary" in hpt["note"], str(hpt))
    check("agent identity picked up from agent.name",
          agg["distinct_agent_identities"]["value"] == ["researcher"],
          str(agg["distinct_agent_identities"]["value"]))


def test_missing_attrs_fixture():
    print("--- missing-attrs fixture (honesty: not measurable) ---")
    m = ingest([MISSING])
    rep = m["ingest"]["files"][0]
    check("1 unparseable row reported explicitly",
          rep["unparseable"] == 1, str(rep["unparseable"]))
    agg = m["aggregate"]
    tok = agg["input_tokens_total"]
    check("tokens NOT MEASURABLE with missing attrs named",
          tok["value"] == "not measurable"
          and "attribute absent" in tok["note"]
          and "gen_ai.usage.input_tokens" in tok["note"], str(tok))
    check("cost NOT MEASURABLE", agg["cost_usd_total"]["value"] ==
          "not measurable")
    ht = agg["human_turns_total"]
    check("human turns NOT MEASURABLE (no markers, no logs stream — "
          "not a claimed zero)", ht["value"] == "not measurable"
          and "logs" in ht["note"], str(ht))
    check("tool_calls_total == 1 measured (unset status = ok per OTLP)",
          agg["tool_calls_total"]["value"] == 1
          and agg["tool_errors_total"]["value"] == 0,
          str(agg["tool_calls_total"]))
    check("llm_calls_total == 1 (call counted even though tokens absent)",
          agg["llm_calls_total"]["value"] == 1)


def test_combined():
    print("--- combined multi-file ingest (mixed coverage => inferred) ---")
    m = ingest([OTLP, FLAT, MISSING])
    agg = m["aggregate"]
    sc = agg["session_count"]
    check("session_count == 4, inferred (2/4 trace-fallback)",
          sc["value"] == 4 and sc["confidence"] == "inferred", str(sc))
    tok = agg["input_tokens_total"]
    check("input tokens 3400 INFERRED with 4/5 coverage note",
          tok["value"] == 3400 and tok["confidence"] == "inferred"
          and "4/5" in tok["note"], str(tok))
    ht = agg["human_turns_total"]
    check("human turns 4 INFERRED (3/4 sessions measurable)",
          ht["value"] == 4 and ht["confidence"] == "inferred"
          and "3/4" in ht["note"], str(ht))
    hpt = agg["human_turns_per_task"]
    check("human_turns_per_task downgraded to inferred under partial "
          "coverage", hpt["confidence"] == "inferred", str(hpt))


def test_cli():
    print("--- ingest_otel.py CLI ---")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "ingest_otel.py"), str(OTLP),
         "--pretty"], capture_output=True, text=True)
    check("exit 0 on valid input", r.returncode == 0, r.stderr[:200])
    try:
        out = json.loads(r.stdout)
        ok = out["aggregate"]["session_count"]["value"] == 2
    except (json.JSONDecodeError, KeyError):
        ok = False
    check("stdout is valid metrics JSON", ok)

    with tempfile.TemporaryDirectory() as td:
        garbage = Path(td) / "garbage.txt"
        garbage.write_text("csv,not,otel\n1,2,3\n")
        r2 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "ingest_otel.py"),
             str(garbage)], capture_output=True, text=True)
        check("exit 2 when nothing parseable", r2.returncode == 2,
              f"rc={r2.returncode}")


def test_merge():
    print("--- merge_telemetry.py ---")
    telemetry = ingest([OTLP])
    snapshot = {
        "schema_version": "1.1",
        "audit_run": {"timestamp": "2026-07-23T00:00:00Z",
                      "project_name": "fixture"},
        "metrics": {
            "autonomy": {
                "intervention_tax": {"value": 0.62,
                                     "confidence": "inferred",
                                     "note": "git-derived fix-up proxy"},
            },
        },
    }
    merged = merge_telemetry.merge(snapshot, telemetry)

    tele = merged["metrics"]["telemetry"]
    check("metrics.telemetry block present with expected keys",
          "human_turns_per_task" in tele and "cost_usd_total" in tele,
          str(sorted(tele)))
    check("telemetry entries carry an otel:<file> source tag",
          tele["human_turns_per_task"].get("source") ==
          "otel:otlp_two_sessions.json",
          str(tele["human_turns_per_task"].get("source")))
    it = merged["metrics"]["autonomy"]["intervention_tax"]
    check("git-derived intervention_tax UNTOUCHED (additive merge)",
          it == snapshot["metrics"]["autonomy"]["intervention_tax"],
          str(it))
    promo = merged["metrics"]["autonomy"].get("human_turns_per_task_otel")
    check("intervention-tax input promoted as *_otel key, measured 1.5",
          promo is not None and approx(promo.get("value"), 1.5)
          and promo.get("confidence") == "measured", str(promo))
    check("dual-lens reminder recorded in telemetry_provenance",
          "INTENDED" in merged["telemetry_provenance"]["note"])

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        snap_p = td / "snapshot.json"
        tel_p = td / "telemetry.json"
        out_p = td / "merged.json"
        snap_p.write_text(json.dumps(snapshot))
        tel_p.write_text(json.dumps(telemetry))

        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "merge_telemetry.py"),
             "--snapshot", str(snap_p), "--telemetry", str(tel_p),
             "--output", str(out_p), "--markdown"],
            capture_output=True, text=True)
        check("CLI exit 0 and merged file written",
              r.returncode == 0 and out_p.exists(), r.stderr[:200])
        check("markdown table has a Source column",
              "| Metric | Value | Confidence | Source |" in r.stdout
              and "otel:" in r.stdout, r.stdout[:200])

        r2 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "merge_telemetry.py"),
             "--snapshot", str(snap_p), "--telemetry", str(tel_p),
             "--output", str(snap_p)], capture_output=True, text=True)
        check("refuses to overwrite the snapshot in place (frozen rule)",
              r2.returncode == 1 and "frozen" in r2.stderr,
              f"rc={r2.returncode}")


def main() -> int:
    print("=== multi-agent-audit telemetry-mode tests ===")
    for p in (OTLP, FLAT, MISSING):
        if not p.exists():
            print(f"fixture missing: {p}", file=sys.stderr)
            return 1
    test_otlp_fixture()
    test_flat_fixture()
    test_missing_attrs_fixture()
    test_combined()
    test_cli()
    test_merge()
    print(f"\n=== Summary: {PASS} pass, {FAIL} fail ===")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
