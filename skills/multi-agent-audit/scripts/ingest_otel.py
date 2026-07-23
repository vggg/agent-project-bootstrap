#!/usr/bin/env python3
"""
ingest_otel.py — Ingest exported OpenTelemetry trace/event FILES and emit
session-level metrics JSON for the multi-agent-audit telemetry mode.

Consumes FILES only — never live endpoints. Zero infra, zero secrets,
reproducible. Accepted input shapes (autodetected per file):

  1. OTLP-JSON        — a JSON object with `resourceSpans` and/or
                        `resourceLogs` (the OTLP `http/json` payload shape;
                        e.g. what an OTel Collector `file` exporter writes,
                        or Claude Code's OTLP export captured to disk).
  2. Flat JSONL       — one JSON object per line; each object is a span or
                        a log-event row. Liberal key handling covers
                        Logfire `records`-table exports (`span_name`,
                        `trace_id`, `start_timestamp`, `attributes`) and
                        Phoenix span-dataframe exports (`name`, `span_kind`,
                        `status_code`, `context.trace_id`,
                        `attributes.<dotted>` flattened columns).
  3. Flat JSON array  — same rows as (2), wrapped in a single JSON list.

Be liberal in what you accept; be explicit about what you could not parse
(per-file `unparseable` count in the output's `ingest.files` block).

Semantic conventions recognized (first match wins, span before event):
  sessions    — `session.id` (Claude Code), `session_id`,
                `gen_ai.conversation.id`; fallback: trace_id (then the
                session-count confidence is downgraded to `inferred`).
  human turns — `claude_code.user_prompt` events (docs:
                https://code.claude.com/docs/en/monitoring-usage),
                `gen_ai.user.message` events, `claude_code.interaction`
                spans (used only when a session has zero user-prompt
                events, to avoid double counting).
  tool calls  — `claude_code.tool` / `claude_code.tool.execution` spans,
                `claude_code.tool_result` events, any record with
                `tool_name` / `tool.name` / `gen_ai.tool.name`, or
                OpenInference `openinference.span.kind == "TOOL"`.
                Deduplicated by `tool_use_id` when present.
  LLM calls   — `claude_code.llm_request` spans, `claude_code.api_request`
                events, any record with `gen_ai.system`, or OpenInference
                span kind `LLM`. Deduplicated/merged by `request_id` /
                `client_request_id` (span wins on conflict; event fills
                gaps — e.g. Claude Code puts cost on the api_request
                event, not on the llm_request span).
  tokens      — `input_tokens`/`output_tokens` (Claude Code),
                `gen_ai.usage.input_tokens`/`.output_tokens` (OTel GenAI
                semconv, e.g. Logfire), `llm.token_count.prompt`/
                `.completion` (OpenInference, e.g. Phoenix).
  cost        — `cost_usd`, `cost_usd_micros` (Claude Code api_request
                event), `gen_ai.usage.cost`. NEVER estimated from token
                counts — absent attrs are reported `not measurable`.
  tasks       — `workflow.run_id` (Claude Code), `task.id`, `task_id`,
                `gen_ai.task.id`. Absent => human-turns-per-task is
                `not measurable (attribute absent)`.

HONESTY RULE (inherited from SKILL.md): every emitted metric carries a
confidence label — `measured` (with source files), `inferred` (with a note
saying why it is partial), or `not measurable` (with the missing attribute
named). Nothing is ever estimated to fill a row.

Usage:
  python3 ingest_otel.py <export-file> [<export-file> ...] \
      [--output <metrics.json>] [--session-attr KEY] [--pretty]

Read-only on inputs. Writes only --output (default: stdout).
Stdlib only; Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

INGESTER_VERSION = "1.0"

# --- attribute conventions -------------------------------------------------

SESSION_ATTR_KEYS = ["session.id", "session_id", "gen_ai.conversation.id",
                     "conversation.id"]
INPUT_TOKEN_KEYS = ["input_tokens", "gen_ai.usage.input_tokens",
                    "gen_ai.usage.prompt_tokens", "llm.token_count.prompt"]
OUTPUT_TOKEN_KEYS = ["output_tokens", "gen_ai.usage.output_tokens",
                     "gen_ai.usage.completion_tokens",
                     "llm.token_count.completion"]
CACHE_READ_KEYS = ["cache_read_tokens", "gen_ai.usage.cache_read_tokens"]
CACHE_CREATE_KEYS = ["cache_creation_tokens",
                     "gen_ai.usage.cache_creation_tokens"]
COST_USD_KEYS = ["cost_usd", "gen_ai.usage.cost"]
COST_MICROS_KEYS = ["cost_usd_micros"]
TOOL_NAME_KEYS = ["tool_name", "tool.name", "gen_ai.tool.name"]
TASK_KEYS = ["workflow.run_id", "task.id", "task_id", "gen_ai.task.id"]
AGENT_KEYS = ["agent.name", "agent_id", "subagent_type", "service.name",
              "user.email"]
MODEL_KEYS = ["model", "gen_ai.request.model", "gen_ai.response.model",
              "llm.model_name"]
REQUEST_ID_KEYS = ["request_id", "client_request_id", "gen_ai.response.id"]

HUMAN_EVENT_NAMES = {"claude_code.user_prompt", "gen_ai.user.message",
                     "user_prompt"}
INTERACTION_SPAN_NAMES = {"claude_code.interaction"}
LLM_SPAN_NAMES = {"claude_code.llm_request"}
LLM_EVENT_NAMES = {"claude_code.api_request"}
TOOL_SPAN_NAMES = {"claude_code.tool", "claude_code.tool.execution"}
TOOL_EVENT_NAMES = {"claude_code.tool_result"}


# --- small helpers ---------------------------------------------------------

def first_attr(attrs: dict, keys: list[str]):
    for k in keys:
        if k in attrs and attrs[k] is not None:
            return attrs[k]
    return None


def to_number(v):
    """Coerce OTLP string-encoded ints / numeric strings to numbers."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except ValueError:
                return None
    return None


def parse_ts(v):
    """Parse a timestamp into epoch seconds (float). None if unparseable.

    Numeric heuristic: >1e17 nanos, >1e14 micros, >1e11 millis, else seconds.
    Strings: numeric strings via the same rule, else ISO 8601.
    """
    if v is None:
        return None
    n = to_number(v)
    if n is not None:
        n = float(n)
        if n > 1e17:
            return n / 1e9
        if n > 1e14:
            return n / 1e6
        if n > 1e11:
            return n / 1e3
        return n
    if isinstance(v, str):
        s = v.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    return None


def iso(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z")


def decode_otlp_value(v: dict):
    if not isinstance(v, dict):
        return v
    if "stringValue" in v:
        return v["stringValue"]
    if "intValue" in v:
        return to_number(v["intValue"])
    if "doubleValue" in v:
        return to_number(v["doubleValue"])
    if "boolValue" in v:
        return v["boolValue"]
    if "arrayValue" in v:
        return [decode_otlp_value(x)
                for x in (v["arrayValue"].get("values") or [])]
    if "kvlistValue" in v:
        return decode_otlp_attrs(v["kvlistValue"].get("values") or [])
    return None


def decode_otlp_attrs(attr_list) -> dict:
    out = {}
    for kv in attr_list or []:
        if isinstance(kv, dict) and "key" in kv:
            out[kv["key"]] = decode_otlp_value(kv.get("value", {}))
    return out


# --- record loading --------------------------------------------------------
# Internal record model: dict with keys
#   kind ("span"|"event"), name, trace_id, span_id, start, end (epoch s),
#   attrs (resource attrs merged under record attrs), status_error (bool),
#   source (file basename)

def _record_status_error(status: dict | None, attrs: dict) -> bool:
    code = (status or {}).get("code")
    if code in (2, "2", "STATUS_CODE_ERROR", "ERROR", "Error", "error"):
        return True
    success = attrs.get("success")
    if isinstance(success, str) and success.lower() == "false":
        return True
    if success is False:  # explicit boolean False => error
        return True
    if attrs.get("error_type"):
        return True
    return False


def records_from_otlp(doc: dict, source: str):
    """Yield internal records from an OTLP-JSON document."""
    records = []
    n_spans = n_events = 0
    has_logs_stream = "resourceLogs" in doc

    for rs in doc.get("resourceSpans") or []:
        res_attrs = decode_otlp_attrs(
            (rs.get("resource") or {}).get("attributes"))
        for ss in rs.get("scopeSpans") or rs.get("instrumentationLibrarySpans") or []:
            for span in ss.get("spans") or []:
                attrs = dict(res_attrs)
                attrs.update(decode_otlp_attrs(span.get("attributes")))
                records.append({
                    "kind": "span",
                    "name": span.get("name") or "",
                    "trace_id": span.get("traceId"),
                    "span_id": span.get("spanId"),
                    "start": parse_ts(span.get("startTimeUnixNano")),
                    "end": parse_ts(span.get("endTimeUnixNano")),
                    "attrs": attrs,
                    "status_error": _record_status_error(
                        span.get("status"), attrs),
                    "source": source,
                })
                n_spans += 1

    for rl in doc.get("resourceLogs") or []:
        res_attrs = decode_otlp_attrs(
            (rl.get("resource") or {}).get("attributes"))
        for sl in rl.get("scopeLogs") or []:
            for lr in sl.get("logRecords") or []:
                attrs = dict(res_attrs)
                attrs.update(decode_otlp_attrs(lr.get("attributes")))
                body = lr.get("body")
                body_s = decode_otlp_value(body) if isinstance(body, dict) \
                    else (body if isinstance(body, str) else None)
                name = (attrs.get("event.name") or lr.get("eventName")
                        or (body_s if isinstance(body_s, str) else "") or "")
                ts = parse_ts(lr.get("timeUnixNano")
                              or lr.get("observedTimeUnixNano"))
                records.append({
                    "kind": "event",
                    "name": name,
                    "trace_id": lr.get("traceId"),
                    "span_id": lr.get("spanId"),
                    "start": ts,
                    "end": None,
                    "attrs": attrs,
                    "status_error": _record_status_error(None, attrs),
                    "source": source,
                })
                n_events += 1

    return records, n_spans, n_events, has_logs_stream


FLAT_NAME_KEYS = ["span_name", "name", "Name"]
FLAT_TRACE_KEYS = ["trace_id", "traceId", "context.trace_id"]
FLAT_SPANID_KEYS = ["span_id", "spanId", "context.span_id"]
FLAT_START_KEYS = ["start_timestamp", "start_time", "startTime", "timestamp",
                   "time"]
FLAT_END_KEYS = ["end_timestamp", "end_time", "endTime"]


def record_from_flat(obj: dict, source: str):
    """Normalize one flat JSONL/array row (Logfire / Phoenix style)."""
    if not isinstance(obj, dict):
        return None
    attrs = {}
    raw_attrs = obj.get("attributes")
    if isinstance(raw_attrs, dict):
        attrs.update(raw_attrs)
    elif isinstance(raw_attrs, list):  # OTLP-style kv list smuggled into JSONL
        attrs.update(decode_otlp_attrs(raw_attrs))
    # Phoenix dataframe exports flatten attrs into dotted columns.
    for k, v in obj.items():
        if isinstance(k, str) and k.startswith("attributes."):
            attrs[k[len("attributes."):]] = v
    # Phoenix span_kind column -> OpenInference kind attr.
    if "span_kind" in obj and "openinference.span.kind" not in attrs:
        attrs["openinference.span.kind"] = obj["span_kind"]

    name = str(first_attr(obj, FLAT_NAME_KEYS) or "")
    start = parse_ts(first_attr(obj, FLAT_START_KEYS))
    end = parse_ts(first_attr(obj, FLAT_END_KEYS))

    event_name = attrs.get("event.name") or obj.get("event.name")
    kind = obj.get("kind")
    is_event = (kind == "event"
                or (isinstance(event_name, str) and event_name != ""))
    if is_event and event_name:
        name = event_name

    status = None
    sc = obj.get("status_code") or obj.get("status")
    if sc is not None:
        status = {"code": sc if not isinstance(sc, dict) else sc.get("code")}

    return {
        "kind": "event" if is_event else "span",
        "name": name,
        "trace_id": first_attr(obj, FLAT_TRACE_KEYS),
        "span_id": first_attr(obj, FLAT_SPANID_KEYS),
        "start": start,
        "end": end,
        "attrs": attrs,
        "status_error": _record_status_error(status, attrs),
        "source": source,
    }


def load_file(path: Path):
    """Load one export file. Returns (records, file_report)."""
    source = path.name
    report = {"path": str(path), "format": None, "spans": 0, "events": 0,
              "unparseable": 0, "has_logs_stream": False, "notes": []}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        report["format"] = "unreadable"
        report["notes"].append(f"could not read file: {e}")
        return [], report

    records: list[dict] = []

    # Whole-file JSON first (OTLP-JSON object, or a flat array).
    doc = None
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        doc = None

    if isinstance(doc, dict) and ("resourceSpans" in doc
                                  or "resourceLogs" in doc
                                  or "resourceMetrics" in doc):
        report["format"] = "otlp-json"
        recs, n_spans, n_events, has_logs = records_from_otlp(doc, source)
        records.extend(recs)
        report["spans"], report["events"] = n_spans, n_events
        report["has_logs_stream"] = has_logs
        if "resourceMetrics" in doc:
            report["notes"].append(
                "resourceMetrics present but not ingested (metrics stream "
                "carries aggregates, not per-session events); use the "
                "spans/logs streams for session-level analysis")
        return records, report

    if isinstance(doc, list):
        report["format"] = "json-array"
        rows = doc
    elif isinstance(doc, dict):
        report["format"] = "json-object"
        rows = [doc]
    else:
        report["format"] = "jsonl"
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                report["unparseable"] += 1

    for row in rows:
        rec = record_from_flat(row, source)
        if rec is None:
            report["unparseable"] += 1
            continue
        records.append(rec)
        if rec["kind"] == "event":
            report["events"] += 1
        else:
            report["spans"] += 1
    if report["unparseable"]:
        report["notes"].append(
            f"{report['unparseable']} row(s) were not parseable JSON "
            "objects and were skipped")
    return records, report


# --- classification --------------------------------------------------------

def is_human_turn_event(rec) -> bool:
    return rec["kind"] == "event" and rec["name"] in HUMAN_EVENT_NAMES


def is_interaction_span(rec) -> bool:
    return (rec["kind"] == "span"
            and (rec["name"] in INTERACTION_SPAN_NAMES
                 or "user_prompt_length" in rec["attrs"]
                 or "user_prompt" in rec["attrs"]))


def is_llm_record(rec) -> bool:
    if rec["kind"] == "span":
        if rec["name"] in LLM_SPAN_NAMES:
            return True
        if "gen_ai.system" in rec["attrs"]:
            return True
        if rec["attrs"].get("openinference.span.kind") == "LLM":
            return True
        return False
    return rec["name"] in LLM_EVENT_NAMES


def is_tool_record(rec) -> bool:
    if is_llm_record(rec) or is_human_turn_event(rec):
        return False
    if rec["kind"] == "span":
        if rec["name"] in TOOL_SPAN_NAMES:
            return True
        if rec["attrs"].get("openinference.span.kind") == "TOOL":
            return True
        return first_attr(rec["attrs"], TOOL_NAME_KEYS) is not None
    return rec["name"] in TOOL_EVENT_NAMES


def session_key(rec, session_attr: str | None):
    """Return (key, method) for grouping a record into a session."""
    if session_attr:
        v = rec["attrs"].get(session_attr)
        if v is not None:
            return str(v), f"attribute {session_attr}"
    v = first_attr(rec["attrs"], SESSION_ATTR_KEYS)
    if v is not None:
        return str(v), "session attribute"
    if rec["trace_id"]:
        return f"trace:{rec['trace_id']}", "trace_id fallback"
    return f"file:{rec['source']}", "file fallback"


# --- metric wrappers (the honesty rule, mechanized) ------------------------

def measured(value, sources, note=None):
    d = {"value": value, "confidence": "measured",
         "source": sorted(set(sources))}
    if note:
        d["note"] = note
    return d


def inferred(value, sources, note):
    return {"value": value, "confidence": "inferred",
            "source": sorted(set(sources)), "note": note}


def not_measurable(note):
    return {"value": "not measurable", "confidence": "not measurable",
            "note": note}


def sum_metric(pairs, sources, absent_note, kind_label):
    """Aggregate (value_or_None) pairs into a labeled sum.

    pairs: list of per-record values, None where the attribute was absent.
    All present  -> measured; some -> inferred (coverage note);
    none present -> not measurable (absent_note).
    """
    present = [v for v in pairs if v is not None]
    if not pairs:
        return not_measurable(
            f"no {kind_label} records in export — {absent_note}")
    if not present:
        return not_measurable(f"attribute absent — {absent_note}")
    total = sum(present)
    if len(present) == len(pairs):
        return measured(total, sources)
    return inferred(
        total, sources,
        f"attribute present on {len(present)}/{len(pairs)} {kind_label} "
        "records; total covers only those — do not extrapolate")


# --- session building + metrics -------------------------------------------

def build_sessions(records, session_attr=None):
    sessions: dict[str, dict] = {}
    for rec in records:
        key, method = session_key(rec, session_attr)
        s = sessions.setdefault(key, {
            "session_id": key, "identity_method": method,
            "records": [], "sources": set(),
        })
        # Prefer the strongest identity method seen for the session.
        if "fallback" not in method and "fallback" in s["identity_method"]:
            s["identity_method"] = method
        s["records"].append(rec)
        s["sources"].add(rec["source"])
    return sessions


def dedupe_tool_records(recs):
    """Merge tool spans + tool_result events by tool_use_id."""
    by_id: dict[str, dict] = {}
    anonymous = []
    for r in recs:
        tid = r["attrs"].get("tool_use_id") or r["attrs"].get(
            "gen_ai.tool.call.id")
        if tid is None:
            anonymous.append(r)
            continue
        cur = by_id.get(str(tid))
        if cur is None or (cur["kind"] == "event" and r["kind"] == "span"):
            # span is the authoritative record; keep error flag from either
            err = r["status_error"] or (cur["status_error"] if cur else False)
            r = dict(r)
            r["status_error"] = err
            by_id[str(tid)] = r
        else:
            cur["status_error"] = cur["status_error"] or r["status_error"]
    return list(by_id.values()) + anonymous


def dedupe_llm_records(recs):
    """Merge llm spans + api_request events by request id (span wins,
    event fills attribute gaps — Claude Code puts cost on the event)."""
    by_id: dict[str, dict] = {}
    anonymous = []
    for r in recs:
        rid = first_attr(r["attrs"], REQUEST_ID_KEYS)
        if rid is None:
            anonymous.append(r)
            continue
        rid = str(rid)
        cur = by_id.get(rid)
        if cur is None:
            by_id[rid] = dict(r, attrs=dict(r["attrs"]))
            continue
        primary, secondary = (cur, r) if cur["kind"] == "span" or \
            r["kind"] == "event" else (r, cur)
        merged_attrs = dict(secondary["attrs"])
        merged_attrs.update(primary["attrs"])   # span attrs win
        primary = dict(primary, attrs=merged_attrs)
        primary["status_error"] = cur["status_error"] or r["status_error"]
        by_id[rid] = primary
    return list(by_id.values()) + anonymous


def record_duration_ms(rec):
    d = to_number(rec["attrs"].get("duration_ms"))
    if d is not None:
        return d
    if rec["start"] is not None and rec["end"] is not None:
        return (rec["end"] - rec["start"]) * 1000.0
    return None


def llm_cost_usd(attrs):
    v = to_number(first_attr(attrs, COST_USD_KEYS))
    if v is not None:
        return v
    m = to_number(first_attr(attrs, COST_MICROS_KEYS))
    if m is not None:
        return m / 1e6
    return None


def compute_session(s, file_reports_by_name):
    recs = s["records"]
    tools = dedupe_tool_records([r for r in recs if is_tool_record(r)])
    llms = dedupe_llm_records([r for r in recs if is_llm_record(r)])
    human_events = [r for r in recs if is_human_turn_event(r)]
    interactions = [r for r in recs if is_interaction_span(r)]

    # Human turns: user-prompt events preferred; interaction spans only as
    # a substitute (never summed — an interaction wraps a user prompt).
    if human_events:
        human_turns = len(human_events)
    elif interactions:
        human_turns = len(interactions)
    else:
        # Only claim a measured zero when at least one contributing file
        # actually exported a logs/events stream.
        has_logs = any(
            file_reports_by_name.get(src, {}).get("has_logs_stream")
            for src in s["sources"])
        human_turns = 0 if has_logs else None

    times = [t for r in recs for t in (r["start"], r["end"])
             if t is not None]
    start = min(times) if times else None
    end = max(times) if times else None

    agents = sorted({str(v) for r in recs
                     for v in [first_attr(r["attrs"], AGENT_KEYS)]
                     if v is not None})
    models = sorted({str(v) for r in llms
                     for v in [first_attr(r["attrs"], MODEL_KEYS)]
                     if v is not None})
    tasks = sorted({str(v) for r in recs
                    for v in [first_attr(r["attrs"], TASK_KEYS)]
                    if v is not None})

    def tok(keys):
        return [to_number(first_attr(r["attrs"], keys)) for r in llms]

    return {
        "session_id": s["session_id"],
        "identity_method": s["identity_method"],
        "source_files": sorted(s["sources"]),
        "start": iso(start),
        "end": iso(end),
        "duration_s": round(end - start, 3)
        if start is not None and end is not None else None,
        "agents": agents,
        "models": models,
        "tasks": tasks,
        "human_turns": human_turns,
        "tool_calls": len(tools),
        "tool_errors": sum(1 for r in tools if r["status_error"]),
        "tool_calls_by_name": _count_by(
            tools, lambda r: str(first_attr(r["attrs"], TOOL_NAME_KEYS)
                                 or r["name"] or "(unnamed)")),
        "llm_calls": len(llms),
        "input_tokens": _sum_or_none(tok(INPUT_TOKEN_KEYS)),
        "output_tokens": _sum_or_none(tok(OUTPUT_TOKEN_KEYS)),
        "cache_read_tokens": _sum_or_none(tok(CACHE_READ_KEYS)),
        "cache_creation_tokens": _sum_or_none(tok(CACHE_CREATE_KEYS)),
        "cost_usd": _sum_or_none([llm_cost_usd(r["attrs"]) for r in llms],
                                 round_to=6),
        "_tok_pairs": {
            "input": tok(INPUT_TOKEN_KEYS),
            "output": tok(OUTPUT_TOKEN_KEYS),
            "cache_read": tok(CACHE_READ_KEYS),
            "cache_creation": tok(CACHE_CREATE_KEYS),
            "cost": [llm_cost_usd(r["attrs"]) for r in llms],
        },
    }


def _count_by(items, keyfn):
    out: dict[str, int] = {}
    for it in items:
        k = keyfn(it)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _sum_or_none(vals, round_to=None):
    present = [v for v in vals if v is not None]
    if not present:
        return None
    total = sum(present)
    if round_to is not None and isinstance(total, float):
        total = round(total, round_to)
    return total


def compute_metrics(records, file_reports, session_attr=None):
    sources = [r["path"] for r in file_reports]
    src_names = [Path(p).name for p in sources]
    reports_by_name = {Path(r["path"]).name: r for r in file_reports}

    sessions_raw = build_sessions(records, session_attr)
    sessions = [compute_session(s, reports_by_name)
                for s in sessions_raw.values()]
    sessions.sort(key=lambda s: (s["start"] or "", s["session_id"]))

    agg: dict[str, dict] = {}

    # session count + identity honesty
    fallback_sessions = [s for s in sessions
                         if "fallback" in s["identity_method"]]
    if not sessions:
        agg["session_count"] = not_measurable(
            "no spans or events could be parsed from the input files")
    elif fallback_sessions:
        agg["session_count"] = inferred(
            len(sessions), src_names,
            f"{len(fallback_sessions)}/{len(sessions)} sessions keyed by "
            "trace_id because no session attribute (session.id / "
            "gen_ai.conversation.id) is present; one trace may not equal "
            "one user session")
    else:
        agg["session_count"] = measured(len(sessions), src_names)

    durations = [s["duration_s"] for s in sessions
                 if s["duration_s"] is not None]
    if durations:
        agg["session_duration_total_s"] = measured(
            round(sum(durations), 3), src_names)
        agg["session_duration_p50_s"] = measured(
            round(statistics.median(durations), 3), src_names)
    else:
        agg["session_duration_total_s"] = not_measurable(
            "attribute absent — no records carried parseable timestamps")
        agg["session_duration_p50_s"] = agg["session_duration_total_s"]

    # tool calls
    n_tools = sum(s["tool_calls"] for s in sessions)
    n_tool_errors = sum(s["tool_errors"] for s in sessions)
    any_spans = any(r["spans"] for r in file_reports)
    if n_tools or any_spans:
        agg["tool_calls_total"] = measured(n_tools, src_names)
        agg["tool_errors_total"] = measured(
            n_tool_errors, src_names,
            note="error = OTLP status ERROR, success=false, or error_type "
                 "present; spans with unset status count as ok (OTLP "
                 "contract: STATUS_CODE_UNSET is not an error)")
        agg["tool_error_rate"] = (
            measured(round(n_tool_errors / n_tools, 4), src_names)
            if n_tools else not_measurable(
                "no tool-call spans/events in export"))
        by_name: dict[str, int] = {}
        for s in sessions:
            for k, v in s["tool_calls_by_name"].items():
                by_name[k] = by_name.get(k, 0) + v
        agg["tool_calls_by_name"] = measured(dict(sorted(by_name.items())),
                                             src_names)
    else:
        agg["tool_calls_total"] = not_measurable(
            "no spans stream in export — tool calls require trace spans "
            "or tool_result events")
        agg["tool_errors_total"] = agg["tool_calls_total"]
        agg["tool_error_rate"] = agg["tool_calls_total"]
        agg["tool_calls_by_name"] = agg["tool_calls_total"]

    # llm calls + tokens + cost
    n_llm = sum(s["llm_calls"] for s in sessions)
    agg["llm_calls_total"] = measured(n_llm, src_names) if sessions else \
        not_measurable("no parseable records")
    tok_specs = [
        ("input_tokens_total", "input",
         "no input-token attribute (input_tokens / "
         "gen_ai.usage.input_tokens / llm.token_count.prompt) on any LLM "
         "record"),
        ("output_tokens_total", "output",
         "no output-token attribute (output_tokens / "
         "gen_ai.usage.output_tokens / llm.token_count.completion) on any "
         "LLM record"),
        ("cache_read_tokens_total", "cache_read",
         "no cache-read-token attribute (cache_read_tokens / "
         "gen_ai.usage.cache_read_tokens) on any LLM record"),
        ("cache_creation_tokens_total", "cache_creation",
         "no cache-creation-token attribute (cache_creation_tokens) on "
         "any LLM record"),
        ("cost_usd_total", "cost",
         "no cost attribute (cost_usd / cost_usd_micros / "
         "gen_ai.usage.cost) on any LLM record; cost is NEVER estimated "
         "from token counts"),
    ]
    for out_key, pair_key, absent_note in tok_specs:
        pairs = [v for s in sessions for v in s["_tok_pairs"][pair_key]]
        m = sum_metric(pairs, src_names, absent_note, "LLM")
        if isinstance(m.get("value"), float):
            m["value"] = round(m["value"], 6)
        agg[out_key] = m

    # human turns (the INTERVENTION TAX input)
    turn_vals = [s["human_turns"] for s in sessions]
    known = [v for v in turn_vals if v is not None]
    if not sessions:
        agg["human_turns_total"] = not_measurable("no parseable records")
    elif not known:
        agg["human_turns_total"] = not_measurable(
            "attribute absent — no user-prompt events "
            "(claude_code.user_prompt / gen_ai.user.message) or "
            "interaction spans in export, and no logs/events stream was "
            "present to confirm a true zero; export the logs stream "
            "(Claude Code: OTEL_LOGS_EXPORTER=otlp) to measure this")
    else:
        total = sum(known)
        if len(known) == len(turn_vals):
            agg["human_turns_total"] = measured(
                total, src_names,
                note="user-prompt events preferred; interaction spans "
                     "counted only for sessions with zero user-prompt "
                     "events (no double counting)")
        else:
            agg["human_turns_total"] = inferred(
                total, src_names,
                f"human turns measurable on {len(known)}/{len(turn_vals)} "
                "sessions (others lacked a logs/events stream); total "
                "covers only those")
        n_meas = len(known)
        agg["human_turns_per_session_mean"] = (
            measured(round(total / n_meas, 4), src_names)
            if len(known) == len(turn_vals) else inferred(
                round(total / n_meas, 4), src_names,
                "mean over the sessions where human turns were "
                "measurable"))

    if "human_turns_per_session_mean" not in agg:
        agg["human_turns_per_session_mean"] = agg["human_turns_total"]

    # human turns per task — only when task-boundary attrs exist
    all_tasks = sorted({t for s in sessions for t in s["tasks"]})
    if all_tasks and known:
        note = (f"{sum(known)} human turns / {len(all_tasks)} distinct "
                "task ids (workflow.run_id / task.id); task COMPLETION "
                "status is not encoded in the export, so this is per "
                "observed task, not per completed task")
        ratio = round(sum(known) / len(all_tasks), 4)
        if len(known) == len(turn_vals):
            agg["human_turns_per_task"] = measured(ratio, src_names,
                                                   note=note)
        else:
            agg["human_turns_per_task"] = inferred(
                ratio, src_names,
                note + "; human turns were only measurable on "
                f"{len(known)}/{len(turn_vals)} sessions")
    else:
        agg["human_turns_per_task"] = not_measurable(
            "attribute absent — no task-boundary attribute "
            "(workflow.run_id / task.id / gen_ai.task.id) on any record"
            if not all_tasks else
            "human turns not measurable (see human_turns_total), so the "
            "per-task ratio cannot be computed")

    agg["distinct_models"] = measured(
        sorted({m for s in sessions for m in s["models"]}), src_names) \
        if sessions else not_measurable("no parseable records")
    agg["distinct_agent_identities"] = measured(
        sorted({a for s in sessions for a in s["agents"]}), src_names,
        note="from agent.name / agent_id / subagent_type / service.name / "
             "user.email attributes") \
        if sessions else not_measurable("no parseable records")

    for s in sessions:
        s.pop("_tok_pairs", None)

    return {
        "telemetry_metrics_version": INGESTER_VERSION,
        "generated": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"),
        "ingest": {"files": file_reports},
        "sessions": sessions,
        "aggregate": agg,
    }


# --- cli -------------------------------------------------------------------

def main(argv):
    ap = argparse.ArgumentParser(
        description="Ingest OTel trace-export files; emit audit telemetry "
                    "metrics JSON.")
    ap.add_argument("files", nargs="+", type=Path,
                    help="OTLP-JSON or flat JSONL/array export files")
    ap.add_argument("--output", type=Path, default=None,
                    help="write metrics JSON here (default: stdout)")
    ap.add_argument("--session-attr", default=None,
                    help="attribute key to group sessions by (overrides "
                         "the built-in session.id conventions)")
    ap.add_argument("--pretty", action="store_true",
                    help="indent the JSON output")
    args = ap.parse_args(argv[1:])

    all_records = []
    file_reports = []
    for p in args.files:
        if not p.exists():
            print(f"error: input file not found: {p}", file=sys.stderr)
            return 1
        recs, report = load_file(p)
        all_records.extend(recs)
        file_reports.append(report)

    if not all_records:
        print("error: no parseable spans or events in any input file",
              file=sys.stderr)
        for r in file_reports:
            print(f"  {r['path']}: format={r['format']} "
                  f"unparseable={r['unparseable']}", file=sys.stderr)
        return 2

    metrics = compute_metrics(all_records, file_reports, args.session_attr)
    out = json.dumps(metrics, indent=2 if args.pretty else None)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out + "\n")
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
