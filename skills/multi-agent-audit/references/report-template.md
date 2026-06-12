# Report template (markdown)

Skeleton for the markdown audit report. Sections in order. Fill every section; if a section has no data, write `_Not available — see Caveats._` rather than omitting.

```markdown
# Multi-agent audit — {{PROJECT_NAME}}

**Audit date:** {{YYYY-MM-DD}}
**Time window:** {{WINDOW_START}} → {{WINDOW_END}} ({{N}} days)
**Auditor:** project-auditor subagent (multi-agent-audit skill v{{SKILL_VERSION}})
**Repos audited:**
- code: {{CODE_REPO_URL}}
- coordination: {{COLLAB_REPO_URL_OR_NA}}

---

## 1. Executive summary

{{Three sentences max. Verdict + headline metric + single biggest opportunity.}}

**Verdict:** {{great-design/faithful | great-design/low-fidelity | weak-design/faithful | weak-design/low-fidelity}}
**Intervention tax:** {{X.XX}} (autonomy split {{Y.YY}})
**Operational fidelity:** {{Z.ZZ}}

---

## 2. Designed model

What the project declares (from Step 0):

- **Layout:** {{layout-family}}
- **Declared roster:** {{N actors}}
  - {{actor 1}} — {{class}}, {{runtime}}
  - {{actor 2}} — ...
- **Backlog source:** {{source}}
- **Coordination substrate:** {{substrate}}
- **Declared guardrails:** {{list}}
- **Declared rituals:** {{list}}

Source documents reviewed:
- {{path 1}}
- {{path 2}}

---

## 3. Drift scorecard + operational fidelity

| Dimension | INTENDED | ACTUAL | GAP | Confidence |
|---|---|---|---|---|
| Agents | {{...}} | {{...}} | {{...}} | {{...}} |
| Autonomy | {{...}} | {{...}} | {{...}} | {{...}} |
| Reviewers | {{...}} | {{...}} | {{...}} | {{...}} |
| Guardrails | {{...}} | {{...}} | {{...}} | {{...}} |
| Routing / ownership | {{...}} | {{...}} | {{...}} | {{...}} |
| Backlog / workflow | {{...}} | {{...}} | {{...}} | {{...}} |
| Rituals | {{...}} | {{...}} | {{...}} | {{...}} |

**Operational fidelity:** {{score}} ({{numerator}} / {{denominator}} dimensions verified)

Interpretation band:
- ≥0.90 — lives as declared
- 0.70–0.89 — meaningful drift on 1–2 dimensions
- 0.50–0.69 — declared model partially aspirational
- <0.50 — declared and actual are different projects

---

## 4. Agent inventory

| Actor | Class | Declared? | Observed? | Identities | Commits | PRs opened | PRs reviewed | Handoffs sent | Notes |
|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

Resolution rules applied: {{persona-prefix-wins, etc.}}
Non-committing agents detected: {{list or "none"}}

---

## 5. Metric tables

### 5.1 Throughput and flow

| Metric | Value | Confidence | Note |
|---|---|---|---|
| Tasks opened / week | {{...}} | {{...}} | {{...}} |
| Tasks closed / week | {{...}} | {{...}} | {{...}} |
| Backlog growth rate | {{...}} | {{...}} | {{...}} |
| Commits / week | {{...}} | {{...}} | {{...}} |
| PRs opened | {{...}} | {{...}} | {{...}} |
| PRs merged | {{...}} | {{...}} | {{...}} |
| Cycle time PR p50 (days) | {{...}} | {{...}} | {{...}} |
| Cycle time PR p90 (days) | {{...}} | {{...}} | {{...}} |

### 5.2 PR review

| Metric | Value | Confidence | Note |
|---|---|---|---|
| Reviews total | {{...}} | {{...}} | {{...}} |
| Distinct reviewers | {{...}} | {{...}} | {{...}} |
| Review latency p50 (h) | {{...}} | {{...}} | {{...}} |
| Merge latency p50 (h) | {{...}} | {{...}} | {{...}} |
| % PRs with zero reviews | {{...}} | {{...}} | {{...}} |
| % self-merges | {{...}} | {{...}} | {{...}} |

### 5.3 Autonomy and intervention tax (headline)

| Metric | Value | Confidence | Note |
|---|---|---|---|
| **Autonomy split** | {{...}} | {{...}} | {{...}} |
| **INTERVENTION TAX** | {{...}} | {{...}} | {{...}} |
| Autonomous initiated tasks | {{...}} | {{...}} | {{...}} |
| Human intervention events | {{...}} | {{...}} | {{...}} |
| — unblock messages | {{...}} | {{...}} | {{...}} |
| — corrections | {{...}} | {{...}} | {{...}} |
| — redos | {{...}} | {{...}} | {{...}} |
| — fix-up commits | {{...}} | {{...}} | {{...}} |

**False-win callout:** {{trigger if autonomy_split > 0.5 AND intervention_tax > 1.0}}

### 5.4 Coordination and network

| Metric | Value | Confidence | Note |
|---|---|---|---|
| Handoffs total | {{...}} | {{...}} | {{...}} |
| Open-handoff age p90 (days) | {{...}} | {{...}} | {{...}} |
| Cross-persona PR comments | {{...}} | {{...}} | {{...}} |
| Top-centrality actor | {{...}} | {{...}} | {{...}} |
| Centrality ratio (top / mean) | {{...}} | {{...}} | {{...}} |

**SPOF callout:** {{trigger if ratio > 2.5}}

### 5.5 DORA

| Metric | Value | Confidence | Note |
|---|---|---|---|
| Lead time p50 (days) | {{...}} | {{...}} | {{...}} |
| Deploy frequency / week | {{...}} | {{...}} | {{...}} |
| Change failure rate | {{...}} | {{...}} | {{...}} |
| MTTR p50 (h) | {{...}} | {{...}} | {{...}} |
| Merge-gate wait p50 (h) | {{...}} | {{...}} | {{...}} |
| Open PRs (window-end snapshot) | {{...}} | {{...}} | {{...}} |

### 5.6 Quality and rework

| Metric | Value | Confidence | Note |
|---|---|---|---|
| Coverage delta (pp) | {{...}} | {{...}} | {{...}} |
| Defect count | {{...}} | {{...}} | {{...}} |
| Rework rate | {{...}} | {{...}} | {{...}} |
| Code churn ratio | {{...}} | {{...}} | {{...}} |
| Acceptance hit rate (sample) | {{...}} | {{...}} | N={{...}} |

### 5.7 Guardrail and ritual efficacy

| Metric | Value | Confidence | Note |
|---|---|---|---|
| Force-pushes observed | {{...}} | {{...}} | {{...}} |
| `add -A` proxy hits | {{...}} | {{...}} | {{...}} |
| Direct main pushes | {{...}} | {{...}} | {{...}} |
| Out-of-scope writes | {{...}} | {{...}} | {{...}} |
| Declared-deny enforcement rate | {{...}} | {{...}} | {{...}} |
| Dev-log adherence | {{...}} | {{...}} | {{...}} |
| Handoff done rate | {{...}} | {{...}} | {{...}} |
| Decision filing rate | {{...}} | {{...}} | {{...}} |

---

## 6. What's working

3–5 items the audit found to be healthy. Preserve these.

1. {{...}}
2. {{...}}
3. {{...}}

---

## 7. Challenges

3–5 issues surfaced by the data. Each with one-line evidence.

1. {{...}} — evidence: {{...}}
2. {{...}} — evidence: {{...}}
3. {{...}} — evidence: {{...}}

---

## 8. Ranked opportunities

Ordered by **leverage × ease** (1–9 score, 9 = highest priority).

| # | What | Why | How | Score |
|---|---|---|---|---|
| 1 | {{...}} | {{...}} | {{...}} | {{9}} |
| 2 | {{...}} | {{...}} | {{...}} | {{6}} |
| 3 | {{...}} | {{...}} | {{...}} | {{4}} |

---

## 9. Scores

| Axis | Score (1–5) | Justification |
|---|---|---|
| Throughput | {{...}} | {{...}} |
| Autonomy (low tax) | {{...}} | {{...}} |
| Coordination | {{...}} | {{...}} |
| Quality / rework | {{...}} | {{...}} |
| Guardrail integrity | {{...}} | {{...}} |
| Knowledge capture | {{...}} | {{...}} |
| Operational fidelity | {{...}} | {{score from §3}} |

**Pattern:** {{great-design/faithful | great-design/low-fidelity | weak-design/faithful | weak-design/low-fidelity}}

**Should the multi-agent overhead be reconsidered?** {{yes/no — if yes, name the alternative (single agent or pure-human) and why}}

---

## 10. Trend

_Populated only if ≥2 snapshots exist._

Compared to {{previous-snapshot-timestamp}}:

| Metric | Previous | Current | Δ | Direction |
|---|---|---|---|---|
| Intervention tax | {{...}} | {{...}} | {{...}} | {{↓ better / ↑ worse}} |
| Operational fidelity | {{...}} | {{...}} | {{...}} | {{...}} |
| Rework rate | {{...}} | {{...}} | {{...}} | {{...}} |
| Merge-gate wait p50 | {{...}} | {{...}} | {{...}} | {{...}} |
| % PRs zero reviews | {{...}} | {{...}} | {{...}} | {{...}} |

**Headline trend:** {{one sentence}}

---

## 11. Methodology

- **Time window:** {{...}}
- **Sources used:** {{gh api, git log, branch protection API, ...}}
- **Sampling:** {{none, or describe stratified-random-by-week N=...}}
- **Identity resolution:** {{persona-prefix-wins, etc.}}
- **Adapters loaded:** {{bootstrap-adapter | heuristic}}
- **Confidence summary:** measured {{N}} | inferred {{M}} | not measurable {{K}}

Reproducibility: every metric value can be re-derived by running the commands cited in this report's tables against a clone of the same state.

---

## 12. Caveats and data gaps

What wasn't measurable, and why. Be specific.

- {{Coverage delta: no coverage reports found in repo}}
- {{MTTR sample: N=4 incidents — too small for stable p50; reported as inferred}}
- {{Slack-channel coordination: external to audit tooling; instructed-only protocols not verifiable}}
- {{...}}

---

*Generated by `multi-agent-audit` skill v{{SKILL_VERSION}}. Skill source: https://github.com/vggg/agent-project-bootstrap/tree/main/skills/multi-agent-audit*
```
