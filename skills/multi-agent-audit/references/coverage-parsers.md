# Coverage parsers (v1.3+)

Companion documentation for `scripts/parse_coverage.py`. Closes the v1.2.0 audit gap: "coverage delta marked not measurable without trying hard."

## Supported formats

| Format | Filename pattern | Source | Parser notes |
|---|---|---|---|
| **Istanbul / nyc / vitest** | `coverage-summary.json` (or any JSON with a `total:` block) | JavaScript/TypeScript via vitest, jest, nyc, c8 | Most reliable — provides lines/branches/functions/statements percentages directly |
| **LCOV** | `lcov.info` | Most JS tools (alt format), some C/C++/Go tools | Plain text; we sum `LF/LH`, `BRF/BRH`, `FNF/FNH` per record |
| **Cobertura XML** | `coverage.xml` | `pytest-cov`, JaCoCo, .NET coverlet | Top-level `<coverage line-rate="..." branch-rate="...">` attributes (0..1, normalized to %) |

## Not supported (yet)

- **Python `coverage.py` binary `.coverage` file** — binary format. Workaround: run `coverage xml` to produce a Cobertura-format export, then parse that. *v1.4 candidate: shell out to `python -m coverage` if available.*
- **JaCoCo binary `.exec`** — same situation; use `jacoco:report` to produce XML.
- **Go's stdlib `cover` profile** — text but format-specific. *v1.4 candidate.*
- **HTML-only reports** (`htmlcov/index.html`) — too fragile to scrape reliably across versions. Recommend the tool emit a structured report alongside.

## Where coverage typically lives in different project types

| Project layout | Likely path |
|---|---|
| JS/TS app (vitest) | `coverage/coverage-summary.json` |
| JS/TS app (nyc) | `coverage/coverage-summary.json` or `.nyc_output/processinfo/index.json` |
| Python (pytest-cov) | `coverage.xml` at repo root, OR `.coverage` binary (use `coverage xml`) |
| Java (JaCoCo) | `target/site/jacoco/jacoco.xml` |
| .NET (coverlet) | `coverage.cobertura.xml` |
| Go | `coverage.out` (text format; not yet supported) |

**Discovery rule (Step 0):** find the first existing file from the priority list:

```bash
for p in \
    coverage/coverage-summary.json \
    coverage-summary.json \
    coverage.xml \
    coverage.cobertura.xml \
    coverage/lcov.info \
    lcov.info \
    target/site/jacoco/jacoco.xml
do
    [ -f "$p" ] && echo "$p" && break
done
```

If none exist, the Coverage-delta metric is `not measurable` and the audit notes the reason: *"No coverage reports found in repo. Suggestion to project owner: emit `coverage/coverage-summary.json` or `coverage.xml` from CI."*

## Computing coverage delta

To measure coverage **change** across the audit window, you need a baseline (start-of-window coverage) AND a current (end-of-window coverage).

For repos that commit coverage reports: read `git show <start-sha>:coverage/...` for the baseline.

For repos that don't commit coverage reports (most): the metric is `not measurable` from a static audit. The auditor can suggest piping coverage to artifacts that the next audit can pull from.

`parse_coverage.py` accepts `--baseline <prior-coverage-file>` and computes the delta when both are supplied:

```bash
# Get baseline from a git commit (read-only)
git -C <repo> show <start-sha>:coverage/coverage-summary.json > /tmp/cov-start.json

# Get current
cp <repo>/coverage/coverage-summary.json /tmp/cov-end.json

# Compute delta
python3 scripts/parse_coverage.py /tmp/cov-end.json --baseline /tmp/cov-start.json
```

Sample output:

```json
{
  "current": {
    "format": "istanbul",
    "lines_pct": 84.7,
    "branches_pct": 81.3,
    "functions_pct": 89.1,
    "statements_pct": 84.7
  },
  "baseline": { ... },
  "delta": {
    "lines_pct": 4.6,
    "branches_pct": 2.8,
    "functions_pct": 5.2,
    "statements_pct": 4.6
  }
}
```

## Integration with the audit's §5.6 Quality/Rework metric

The coverage row in §5.6 should look like:

| Metric | Value | Confidence | Note |
|---|---|---|---|
| Coverage delta (lines) | +4.6 pp | measured | Istanbul format; baseline from start-of-window commit |

If `--baseline` is omitted, only the current coverage is reported (delta = `not measurable`).

## Confidence labels

- `measured` — current and baseline both parsed from a real coverage report.
- `inferred` — only current available; baseline approximated (e.g., taking commit-count delta as a proxy for test-volume change).
- `not measurable` — no coverage reports present.

Never fabricate. A row of `not measurable, reason: no coverage reports in repo` is more useful than a guessed number.

## Recommended path for projects without coverage reports

If the project owner wants future audits to track coverage deltas:

1. Configure CI to emit a coverage report on every push to main.
2. **Commit the report file** (or upload as a workflow artifact retained for ≥1 audit window).
3. Re-run the audit. The next audit picks up the format and starts tracking deltas.

This is a project-side change, not a skill change. The audit's job is to detect and report; configuring CI is a follow-up the human owns.
