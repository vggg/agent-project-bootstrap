# Confidence labels + snapshot schema + trend mode

How to label uncertainty per metric, what to persist for future audits, and how to read deltas between snapshots.

## Confidence labels (canonical)

Every numeric value in the report carries one of three labels:

| Label | When to use |
|---|---|
| **measured** | The value was computed from an independent, reproducible source. The command is in the methodology. |
| **inferred** | The value is proxy-based, sampled, or computed from incomplete data. Useful but caveat in the note. |
| **not measurable** | The data needed isn't accessible (private platform, missing reports, declared in a system the audit can't see). Report the reason. |

**Don't fabricate** a value just to fill a row. Empty rows with `not measurable` and a reason are more honest and more useful than guessed numbers.

### Aggregate reporting

In the report's executive summary and methodology, sum the labels:

> *Confidence summary: 47 metrics — measured: 32 (68%) | inferred: 11 (23%) | not measurable: 4 (9%).*

If `measured` drops below ~60% of total, the report's executive summary should say so up front — the audit's verdict carries less weight when the data carries less weight.

## Snapshot JSON schema

Every audit run persists a machine-readable snapshot to `<output>/snapshots/<YYYY-MM-DDTHHMMSS>.json` for trend analysis. Schema (v1):

```json
{
  "schema_version": "1.0",
  "audit_run": {
    "timestamp": "2026-06-12T14:30:00Z",
    "project_name": "GardenTwin",
    "audited_repos": [
      { "role": "code", "url": "https://github.com/ArkShark11/GardenTwin" }
    ],
    "time_window": { "start": "2026-03-14", "end": "2026-06-12", "days": 90 },
    "auditor": {
      "skill_version": "1.0.0",
      "subagent": "project-auditor",
      "runtime": "claude-code"
    },
    "methodology_notes": "Stratified-by-week PR sample of 100/412"
  },
  "agent_inventory": [
    {
      "actor": "Iris",
      "class": "hybrid",
      "declared": true,
      "observed": true,
      "identities": ["iris@vault.local", "vikram.godbole@..."],
      "metrics": { "commits": 47, "prs_opened": 0, "prs_reviewed": 0, "handoffs_sent": 12 },
      "notes": null
    }
  ],
  "drift_scorecard": [
    {
      "dimension": "Agents",
      "intended": "5 declared",
      "actual": "6 observed (+1 dependabot, undeclared)",
      "gap": "+1 shadow agent; 1 declared dormant",
      "confidence": "measured"
    }
  ],
  "operational_fidelity": {
    "score": 0.74,
    "numerator": 5.18,
    "denominator": 7,
    "dimensions_scored": 7
  },
  "metrics": {
    "throughput": {
      "tasks_opened_per_week": { "value": 8.2, "confidence": "measured" },
      "tasks_closed_per_week": { "value": 7.1, "confidence": "measured" },
      "prs_merged": { "value": 28, "confidence": "measured" },
      "cycle_time_pr_p50_days": { "value": 2.3, "confidence": "measured" },
      "cycle_time_pr_p90_days": { "value": 7.1, "confidence": "measured" }
    },
    "pr_review": {
      "reviews_total": { "value": 49, "confidence": "measured" },
      "review_latency_p50_hours": { "value": 4.8, "confidence": "measured" },
      "pct_prs_with_zero_reviews": { "value": 0.07, "confidence": "measured" },
      "pct_self_merges": { "value": 0.12, "confidence": "measured" }
    },
    "autonomy": {
      "autonomy_split": { "value": 0.41, "confidence": "measured" },
      "intervention_tax": { "value": 0.62, "confidence": "inferred", "note": "Fix-up window default 7d; sampled corrections N=30" },
      "human_intervention_events": { "value": 18, "confidence": "measured" },
      "autonomous_initiated_tasks": { "value": 29, "confidence": "measured" }
    },
    "coordination": {
      "handoffs_total": { "value": 41, "confidence": "measured" },
      "handoffs_open_age_p90_days": { "value": 12, "confidence": "measured" },
      "centrality_top_actor": { "value": "Vikram", "confidence": "measured" },
      "centrality_top_ratio": { "value": 3.1, "confidence": "measured" }
    },
    "dora": {
      "lead_time_p50_days": { "value": 2.3, "confidence": "measured" },
      "deploy_frequency_per_week": { "value": 3.1, "confidence": "inferred", "note": "Proxy: merges-to-main; no release-tag stream" },
      "change_failure_rate": { "value": 0.11, "confidence": "inferred" },
      "mttr_p50_hours": { "value": 5.2, "confidence": "inferred", "note": "Sample N=4 incidents" }
    },
    "quality_rework": {
      "coverage_delta_pct": { "value": "not measurable", "confidence": "not measurable", "note": "No coverage reports in repo" },
      "defect_count": { "value": 23, "confidence": "measured" },
      "rework_rate": { "value": 0.09, "confidence": "measured" },
      "acceptance_hit_rate": { "value": 0.85, "confidence": "inferred", "note": "Sample N=10 PRs" }
    },
    "guardrail_ritual": {
      "force_pushes_observed": { "value": 2, "confidence": "measured" },
      "direct_main_pushes": { "value": 0, "confidence": "measured" },
      "out_of_scope_writes": { "value": 3, "confidence": "measured" },
      "declared_deny_enforcement_rate": { "value": 0.43, "confidence": "measured" },
      "dev_log_adherence": { "value": 0.58, "confidence": "measured" },
      "handoff_done_rate": { "value": 0.79, "confidence": "measured" }
    }
  },
  "scores": {
    "throughput": { "score": 4, "justification": "Sustained cadence; cycle time p50 < 3 days; minor backlog growth" },
    "autonomy_low_tax": { "score": 3, "justification": "Autonomy split 0.41 with intervention tax 0.62 — middling; tax above ideal" },
    "coordination": { "score": 3, "justification": "Handoff volume proportionate; one moderate SPOF (Vikram, 3.1x mean centrality)" },
    "quality_rework": { "score": 4, "justification": "Low rework rate (9%); acceptance hit 85%; lead time tight" },
    "guardrail_integrity": { "score": 2, "justification": "Declared-deny enforcement only 43%; force-pushes observed twice" },
    "knowledge_capture": { "score": 4, "justification": "Wiki current; decisions filed; dev-log adherence 58% (gap)" },
    "operational_fidelity": { "score": 4, "justification": "0.74 — meaningful drift; one or two specific gaps to close" }
  },
  "verdict": {
    "pattern": "great-design / low-fidelity",
    "summary": "Architecture is sound; declared guardrails are mostly markdown-only. Operational fix not design fix."
  },
  "ranked_opportunities": [
    {
      "rank": 1,
      "what": "Enable GitHub branch protection on main with required reviews",
      "why": "Promotes 2 declared denies (force-push, direct push) from instructed to enforced",
      "how": "gh api -X PUT repos/.../branches/main/protection ... — one configuration step",
      "leverage_ease_score": 9
    }
  ]
}
```

The schema is permissive: optional fields can be omitted; unknown fields are ignored by the trend-mode reader (so future audits can add fields without breaking history).

## Trend mode

When the auditor runs against a project that has ≥2 prior snapshots in the same output location, it enters **trend mode**:

1. Load the most recent snapshot (the **baseline**).
2. Load the second-most-recent (the **previous**).
3. Compute deltas on the key trend metrics:
   - `intervention_tax`
   - `rework_rate`
   - `merge_gate_wait_p50_days`
   - `operational_fidelity.score`
   - `pct_prs_with_zero_reviews`
4. Render the Trend section in the report:

```markdown
## Trend

Compared to the prior audit (<previous-timestamp>):

| Metric | Previous | Current | Δ | Direction |
|---|---|---|---|---|
| Intervention tax | 0.81 | 0.62 | −0.19 | ↓ better |
| Operational fidelity | 0.62 | 0.74 | +0.12 | ↑ better |
| Rework rate | 0.14 | 0.09 | −0.05 | ↓ better |
| Merge-gate wait p50 | 8.1h | 4.8h | −3.3h | ↓ better |
| PRs with zero reviews | 18% | 7% | −11pp | ↓ better |

Headline: intervention tax down 23%; project moving from great-design/low-fidelity toward great-design/faithful.
```

In the HTML dashboard, the same data renders as sparklines under each metric card.

## Time-window normalization

Snapshots may use different windows (90-day audit followed by 30-day audit). Normalize before computing deltas:

- For **rate** metrics (per-week values, percentages, ratios): compare directly.
- For **count** metrics (PRs merged, commits): normalize to per-day or per-week before delta.
- For **percentile** metrics (cycle time p50): compare directly but note the window mismatch.

If windows differ by >2x, surface a note in the Trend section: *"Window sizes differ significantly (90d vs 30d); rate metrics compared directly, count metrics shown as per-week."*

## What NOT to put in snapshots

- Free-text commentary from the report — the snapshot is structured data, not the report.
- Raw command output (logs, full git outputs) — too verbose; not useful for trend reading.
- Identifying information beyond what the human invoker already has access to (snapshots may be checked into a collab repo).

## Snapshot location

Per `SKILL.md § Output location convention`:

- For collab-repo projects: `<collab-repo>/audit/snapshots/<timestamp>.json`
- For single-repo projects: `~/Workspace/audit-reports/<project>/snapshots/<timestamp>.json`

**Never** write the snapshot inside the audited repos themselves. The snapshot is auditor output, not project artifact.

## Forward compatibility

The `schema_version` field allows the snapshot reader to handle older snapshots. v1.0 is the current spec. Breaking changes bump to v2.0; additive changes bump to v1.1, v1.2.

When reading a snapshot:

1. Check `schema_version`.
2. If unsupported, skip with a note: *"Snapshot at <path> has unsupported schema v<X>; not included in trend."*
3. Otherwise, read all known fields; ignore unknown ones.
