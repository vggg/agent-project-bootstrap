---
name: multi-agent-audit
description: Use when the user asks to audit, assess, review, evaluate, or measure a multi-agent (agentic / autonomous-agent) project or team — including questions like "is this multi-agent setup actually working?", "what's our intervention tax?", "are the agents earning their keep?", or any request to collect agent collaboration metrics, score the project's efficacy, judge whether autonomy is paying off, or produce an evidence-based grade of a project that mixes human and autonomous agents. Read-only — grades the project, never changes it.
---

# multi-agent-audit

A **read-only** workflow for grading whether a project that mixes HUMAN and AUTONOMOUS agents is actually working — with evidence and numbers, not vibes. Output: a scored efficacy report (markdown + optional HTML) and a machine-readable snapshot for trend analysis.

Sister skill to `agent-project-bootstrap`: bootstrap **builds** multi-agent projects; this skill **grades** them.

## Non-negotiable principle — read-only

This skill grades the audited project. It never changes it.

- No edits, commits, pushes, PRs, or backlog/config changes to the audited repos.
- Only read files and run read-only queries: `git log`, `git diff`, `git shortlog`, `gh ... list / view`, `gh api GET`.
- The ONLY thing this skill may write is its own report and snapshot files, in a location **OUTSIDE** the audited repos.
- If any step in the workflow would mutate the audited project, **skip it and record why in the report's "Caveats / data gaps" section.**

When used via the `project-auditor` subagent (`agents/project-auditor.md`), the tool allow-list enforces this at the runtime level (no `Edit` granted; `Write` permitted only for the report file). When used directly from a Claude Code session without the subagent, the human invoker is responsible for not letting the audit make changes — re-read the rule each step.

## Two-layer + framework-neutral

This skill must work on different multi-agent stacks: `agent-project-bootstrap` collab-repo layouts, CrewAI, LangGraph, AutoGen, Copilot agents, custom loops. The skill is structured in **two layers**:

- **Universal (what to measure)** — the metric taxonomy, scoring rubric, dual-lens drift model, and report template are the same across frameworks. See `references/metric-taxonomy.md` and `references/drift-analysis.md`.
- **Per-layout (where to find data)** — file paths, manifest formats, and platform queries vary. **Discover the layout first** (Step 0), then map the universal metrics onto the data sources you find. For known layouts, load the matching adapter reference:
  - `references/bootstrap-adapter.md` — `agent-project-bootstrap` v1.x collab-repo layout (`manifest.yaml`, `persona.yaml`, `_handoff/`, `adapters/<runtime>/`, `agents/<persona>/`, `decisions/`, `findings/`, `wiki/`).
  - For other frameworks (CrewAI, LangGraph, AutoGen): discover heuristically. Future versions will add dedicated adapter references.

## Inputs to confirm before starting

Before any data gathering, confirm with the human:

1. **Repo path(s) or URL(s)** — code repo and coordination/collab repo if separate.
2. **Backlog source** — GitHub issues, Linear, Jira, vault-tracked, or none.
3. **Platform host and auth** — `github.com` vs GHE; confirm `gh auth status` works for the target repos. PR mining requires this.
4. **Optional `actors.yaml`** — if the human declares the agent roster (especially non-committing agents like PR-review bots or cron librarians), pass that file in. Template at `assets/actors.example.yaml`.
5. **Time window** — last 30 days, last 90 days, custom range, or all-time. Default: last 90 days. **If the audit purpose is to measure the impact of a specific event (workforce change, process change), surface this trade-off and consider tuning the window to bracket the event.**
6. **Output format** — markdown only, markdown + HTML dashboard, or short-form. Default: markdown + HTML (v1.3+).
7. **Per-persona scorecards** — yes/no. Default: yes if ≥3 personas are detected.
8. **Snapshot output location** — where to write the report and snapshot JSON. **Must be outside the audited repos.** Default: the audited project's *coordination/collab repo* if one exists (e.g., for `agent-project-bootstrap` layouts the collab repo's `audit/` folder), or `~/Workspace/audit-reports/<project>/` otherwise.
9. **Auditor independence** — is the invoking auditor (Claude Code session OR the `project-auditor` subagent) itself a participant in the audited project (e.g., one of the declared personas)? If yes, capture the participant_personas list and surface the conflict-of-interest in §11 Methodology. **Honesty rule** (v1.3+): a participant auditor's findings on Agents / Coordination / Knowledge-capture dimensions may be skewed; flag, do not suppress.
10. **Operational fidelity weighting** — default (equal weight across dimensions) or weighted (caller supplies per-dimension weights, OR uses the v1.3 default weights — see `references/metric-taxonomy.md § Operational fidelity weighting`).
11. **Timeline events** — include a §9.5 Timeline section? Default: yes. See `references/timeline.md` for the event taxonomy.

Use HTTPS for any clone. Do not configure git identity in audited repos.

## Workflow

Numbered to match the original spec (Step 2 is intentionally elided — discovery+drift fold into Step 0.5; scoring is Step 3).

### Step 0 — Discovery

Profile the audited project without assuming layout. Identify:

- The declared agent roster (human + autonomous).
- How work is tracked (issue tracker, branch labels, kanban, vault notes).
- How agents coordinate (handoff files, PR comments, channel messages, structured docs).
- How autonomy is driven and gated (cron, webhook, manual invoke; approval gates, rate limits).
- Declared guardrails (deny-lists, tool allow-lists, approval rules, code-owners).

**Record absences as findings, not silences.** A project with no declared roster, or no documented coordination protocol, or no guardrail declaration is itself diagnostic data — log it and surface in the report's caveats.

Full procedure: `references/discovery.md`.

### Step 0.5 — Agent Inventory + DUAL-LENS pass

> Do not skip this step. This is where audits fail — by collapsing what a project *says* it does into what the auditor *observes* it doing.

#### Agent Inventory

Enumerate actors from ALL sources, not just `git log --all --format='%an'`:

- Git committers and PR authors.
- **PR reviewers** (often missed) — including bot accounts and Apps.
- Mergers.
- CI/bot/App identities visible in webhook deliveries, Actions, or GitHub Apps.
- The declared roster (`actors.yaml`, `manifest.yaml`, persona files, COORDINATION.md tables).
- The coordination substrate (handoff `from:` / `for:` fields, dev-log `agent:` frontmatter).

**Detect non-committing agents.** A PR-review bot, a cron librarian whose work lands in the vault, an approval-only persona, a chat-driven analyst that never opens a PR — these are real agents whose work doesn't show in `git log` but shapes the project. Missing them inflates the autonomy-split metric and hides the intervention tax.

Classify each actor: `human | autonomous | hybrid`. Resolve one persona ↔ many identities into canonical actors (a persona may commit under multiple email addresses; a human may also act as a librarian-in-name).

Full procedure: `references/actor-resolution.md`.

#### DUAL-LENS / DRIFT

For **every** dimension below, report three values with a confidence label:

| Lens | Meaning |
|---|---|
| **INTENDED** | What the project declares — from CONVENTIONS.md, persona.yaml, roster files, COORDINATION docs. |
| **ACTUAL** | What the auditor independently verifies — from git history, gh API, file content. |
| **GAP** | The delta. Plain language. |

Cover these dimensions:

- **Agents** — declared roster vs observed actors.
- **Autonomy** — what's declared as autonomous vs what runs without human intervention.
- **Reviewers** — declared reviewers vs who actually reviews.
- **Guardrails** — declared deny-lists vs what's enforced by the tool allow-list at runtime.
- **Routing / ownership** — declared persona scope vs observed write patterns.
- **Backlog / workflow** — declared ticketing flow vs observed PR-issue linkage.
- **Rituals** — declared session-start checks, dev-log conventions, handoff protocols vs observed adherence.

**Never collapse declared into observed.** A reviewer declared in `CONVENTIONS.md` who has 0 reviews in the time window is a **declared-but-not-operationalized** drift — the report must surface it explicitly.

Three drift archetypes to watch for:

1. **Declared but not operationalized** — e.g., a librarian persona declared in the roster, with no commits/wiki updates in the window.
2. **Observed but undeclared** — e.g., a shadow bot opening PRs without appearing in the declared roster. Often a CI/CD App.
3. **Instructed-only vs enforced** — declared deny-lists that the runtime tool allow-list doesn't actually block. *"Don't force-push"* in CONVENTIONS.md is instruction; the actual block is whether the runtime's tool set excludes the means to force-push. Check the deny against the granted tools.

Emit:

- A **DRIFT SCORECARD** — one row per dimension, with INTENDED / ACTUAL / GAP / confidence.
- An **OPERATIONAL FIDELITY score** — the fraction of the declared model that the audit verifiably observed running. Range: 0.00–1.00. Round to two decimals. Show the numerator (verified declarations) over denominator (total testable declarations).

Full procedure and worked example: `references/drift-analysis.md`.

### Step 1 — Metrics

Mine the **platform**, not just the git clone. The git history under-counts: it misses PR review activity, issue triage, scheduled-action runs, and the work of non-committing agents. Use `gh api` for anything that requires platform context.

For each metric:

- Show the **command or source** that produced it.
- Show the **raw number** (or rate).
- Tag with a **confidence label**: `measured | inferred | not measurable`.
- If not computable, write `"not measurable"` and the reason — **never fabricate**.

Categories to cover:

#### Throughput and flow

- Tasks opened, closed, in-progress; backlog growth rate.
- Commits per author per week.
- PRs opened / merged / rejected / abandoned.
- Cycle time p50 / p90 (PR opened → merged; issue created → closed).

#### PR review and review-agent activity

- Reviews (count, by reviewer including bots).
- Review rounds per PR (p50, p90).
- Catch rate (issues raised in review per 1k lines reviewed; rough proxy).
- Review latency (PR opened → first review).
- Merge latency (last approving review → merge).

Use `gh api repos/<owner>/<repo>/pulls/<n>/reviews` per PR (loop for the time window). See `references/platform-integrations.md`.

#### Autonomy split + INTERVENTION TAX (the headline)

**Autonomy split** = fraction of tasks (commits, PRs, decisions, handoffs) initiated by autonomous agents.

**INTERVENTION TAX** = human touches per autonomous task. Counts:

- Unblock messages (human responses to an autonomous agent that was stuck).
- Corrections (human-authored commits that follow an autonomous agent's work in the same logical unit and modify the same files).
- Redos (human-led PRs that supersede a closed autonomous PR within N days; default N=7).
- Fix-up commits — human commits with messages matching `fix:`, `chore: fix`, `revert:`, `hotfix:` that follow an autonomous commit on the same files within N days.

**A high autonomy split with a high intervention tax is a false win.** The headline number is the *ratio* of human-touches to autonomous-tasks; lower is better. Report alongside (not instead of) the autonomy split.

#### Coordination overhead + NETWORK analysis

- Handoff volume (files in `_handoff/`, by `from:` × `for:`).
- Cross-persona PR comments.
- Cross-clone merge activity (when two devs share a code repo).
- Build a network graph: nodes = actors, edges = handoffs / review-edges / merge-edges. Compute centrality — a single high-centrality node is a single point of failure (often Vikram or the librarian).

Full procedure: `references/advanced-metrics.md`.

#### DORA + flow

- Lead time for changes (commit → deploy or PR-open → merge as a proxy).
- Deploy frequency (release tags or main merges per week).
- Change failure rate (reverts + hotfixes / total deploys).
- Mean time to recovery (revert/hotfix latency from the bad change).
- Merge-gate wait (PR ready-for-review → merged, excluding the work-in-progress time).
- Work in progress (open PRs over time).

#### Quality and rework

- Coverage delta over the window (if a coverage report exists).
- Defect count (issues labelled `bug` opened in the window).
- Rework rate — `git log --grep='revert\|fix-up\|hotfix'` over commits in the window.
- Code churn — `git log --shortstat` aggregated.
- **Acceptance hit rate on a sample.** Pick N closed PRs (default N=10); for each, did the merged code match the issue's acceptance criteria as written? Surface as a percentage with a confidence label.

#### Guardrail and ritual efficacy

- Force-push events on protected branches (via gh api branch-protection-rule violations, if available).
- `git add -A` evidence (large commits touching many files — proxy).
- Push-to-main events (PR merges to main / direct commits to main; if the project declares "no direct push to main," any direct main commit is a drift).
- Out-of-scope actions — a persona writing outside its declared write area (per its `persona.yaml` or COORDINATION.md write-ownership table).
- Enforced vs instructed — for each declared deny, is there a tool-level block (allow-list) or only an instruction (CONVENTIONS.md text)?
- Ritual adherence — does the project's session-start checklist actually get followed? (Look for the expected first-N actions in a session.) Are dev-logs written per the convention? Are decisions filed where declared?

Full taxonomy and 1–5 scoring rubric per metric: `references/metric-taxonomy.md`.
Confidence labels and snapshot persistence: `references/confidence-and-trends.md`.

### Step 3 — Score

Score 1–5 per axis, with a one-line justification per score:

| Axis | What it grades |
|---|---|
| **Throughput** | Are tasks moving through? Is the cadence sustained? |
| **Autonomy (low tax)** | Is the autonomy split real (i.e., earned), with low intervention tax? |
| **Coordination** | Is handoff overhead proportionate to throughput, or drowning it? |
| **Quality / rework** | Does work stick, or get re-done? |
| **Guardrail integrity** | Are declared guardrails actually enforced? |
| **Knowledge capture** | Are decisions, findings, and dev-logs accumulating usefully, or stale? |
| **Operational fidelity** | The OPERATIONAL FIDELITY score from Step 0.5 — fraction of declared model verifiably live. |

Rubric per axis in `references/metric-taxonomy.md`.

Overall verdict must speak to **both lenses**:

- *Sound AS DESIGNED?* — Is the architecture coherent and well-intentioned?
- *Delivering AS OPERATING?* — Is what's actually running good enough to justify the design's overhead?

Name the failure mode if there is one:

- **great-design / low-fidelity** — beautiful spec, weakly executed. Fix is operational.
- **weak-design / faithful** — what's declared is what runs, but it shouldn't have been declared this way. Fix is design.
- **great-design / faithful** — the project is working. Verdict: keep going.
- **weak-design / low-fidelity** — incoherent and unexecuted. Verdict: consider whether the multi-agent overhead is earning its keep; a single agent or pure-human flow may be better.

Surface "when a single agent or pure-human flow would have been better" explicitly — the audit must be willing to recommend ABANDONING the multi-agent setup if the numbers say so.

### Step 4 — Report

Default: a markdown report at `<output>/<project>-audit-<YYYY-MM-DD>.md`, using `references/report-template.md` as the structure.

Sections (in order):

1. **Executive summary** — 3 sentences max. The verdict + the headline metric + the single biggest opportunity.
2. **Designed model** — what the project declares (from Step 0).
3. **DRIFT scorecard + operational fidelity** — the table from Step 0.5.
4. **Agent inventory** — declared + observed actors, classified, with identities resolved.
5. **Metric tables** — one per category from Step 1, each row tagged with a Confidence column.
6. **What's working** — 3–5 things to preserve.
7. **Challenges** — 3–5 issues with evidence.
8. **Ranked opportunities** — what to change, ordered by leverage × ease.
9. **Scores** — the 1–5 axis scores with justifications.
10. **Trend** — only if ≥2 snapshots exist (deltas on intervention tax, rework, merge-gate wait, operational fidelity).
11. **Methodology** — sources, commands, time window, what was sampled vs measured exhaustively.
12. **Caveats / data gaps** — what wasn't measurable and why.

Optionally also produce: a self-contained flat HTML + Chart.js dashboard at `<output>/<project>-audit-<YYYY-MM-DD>.html` using `assets/report-template.html`. Visuals:

- Autonomy donut (human vs autonomous task share).
- Per-persona bars (commits, reviews, handoffs).
- Throughput trend (commits + PRs per week).
- DORA cards (lead time, deploy freq, change-fail rate, MTTR).
- Drift table (the scorecard from Step 0.5).
- Agent-inventory table.
- Review/merge network (force-directed).
- Score radar (1–5 across the seven axes).

**Persist a machine-readable snapshot** to `<output>/snapshots/<YYYY-MM-DDTHHMMSS>.json` containing:

- All numerical metrics with their confidence labels.
- The drift scorecard.
- The axis scores.
- The time window and methodology metadata.

Snapshot schema in `references/confidence-and-trends.md`.

When ≥2 snapshots exist for the same project, the report's **Trend** section computes deltas (intervention tax, rework rate, merge-gate wait, operational fidelity) and visualizes them as small sparklines in the HTML dashboard.

## Files in this skill

```
skills/multi-agent-audit/
  SKILL.md                            # this file (orchestrator)
  references/
    discovery.md                      # Step 0 procedure
    actor-resolution.md               # Step 0.5 actor enumeration
    drift-analysis.md                 # Step 0.5 dual-lens scoring (v1.3: multi-substrate Agents)
    metric-taxonomy.md                # universal metric definitions + 1-5 rubric + v1.3 weighting
    platform-integrations.md          # gh / CI / coverage queries (read-only)
    advanced-metrics.md               # DORA + network analysis
    confidence-and-trends.md          # confidence labels + snapshot v1.1 schema + trend mode + addenda
    bootstrap-adapter.md              # agent-project-bootstrap v1.x layout mining (v1.3: 5-substrate persona attribution)
    timeline.md                       # v1.3 — important-events taxonomy + extraction rules
    report-template.md                # markdown report skeleton (v1.3: §9.5 timeline + §11b addenda + independence)
    coverage-parsers.md               # v1.3 — Istanbul / vitest / lcov / cobertura / Python coverage formats
    short-form-mode.md                # v1.3 — single-page executive-summary mode
  assets/
    actors.example.yaml               # roster declaration template
    report-template.html              # Chart.js dashboard template (v1.3: timeline + addenda + per-persona scorecards)
  scripts/
    collect_git_metrics.sh            # read-only git metric collection (v1.3: conv-commits filter)
    trend_reader.py                   # v1.3 — reads snapshots/; emits §10 Trend section
    extract_timeline.py               # v1.3 — extracts important events; emits §9.5 Timeline
    compute_centrality.py             # v1.3 — betweenness centrality on the coordination network
    parse_coverage.py                 # v1.3 — coverage delta from common report formats
    render_report.py                  # v1.3 — renders the HTML dashboard from snapshot + template
    persona_attribution.py            # v1.3 — per-persona PR attribution via the multi-substrate lens
  tests/
    subagent_isolation_smoke.md       # v1.3 — verifies the project-auditor subagent can't write to audited repos
  agents/
    project-auditor.md                # subagent definition (Claude Code)
```

## How to invoke

### From Claude Code, via the subagent (recommended — enforces read-only)

```
Use the project-auditor subagent to audit <project>.
```

The subagent loads this skill, confirms inputs, runs Steps 0 → 4, writes the report outside the audited repos.

### From Claude Code, directly

Read this SKILL.md and follow the workflow. The read-only rule is your responsibility — no `Edit` operations on the audited repos.

### From code-puppy or other runtimes

The references and scripts in this skill are pure markdown and pure bash — runtime-neutral. Invoke by reading `skills/multi-agent-audit/SKILL.md` from the cloned `agent-project-bootstrap` repo and following the workflow. The subagent file (`agents/project-auditor.md`) is Claude-Code-specific; for other runtimes, restrict tool access through the runtime's native mechanism (code-puppy: declare the agent with a read-only tool allow-list per its convention).

## Output location convention

This skill writes outputs to a location **outside** the audited project. Default rules:

1. **If the audited project has a coordination/collab repo** (e.g., `agent-project-bootstrap` collab-repo-project layout, VANAR's `vanar-collab`) — write to `<collab-repo>/audit/<project>-audit-<YYYY-MM-DD>.{md,html}` and `<collab-repo>/audit/snapshots/<timestamp>.json`. The audit directory is a normal part of the collab substrate; commit and push via the collab repo's standard workflow (a human commits the audit output — the skill does not).
2. **If the audited project is single-repo** (no separate collab repo, e.g., GardenTwin) — write to `~/Workspace/audit-reports/<project>/<project>-audit-<YYYY-MM-DD>.{md,html}` and `~/Workspace/audit-reports/<project>/snapshots/<timestamp>.json`. The human optionally commits these to a personal reports repo.

The skill never commits or pushes the report itself. It only writes the files; the human reviews and chooses where to publish.

## Headline metric reminder

If you remember nothing else from this skill: **the intervention tax is the headline.** A multi-agent project with a high autonomy split and a high intervention tax is doing more work than a single-agent or pure-human equivalent would have. The audit's job is to surface that honestly.
