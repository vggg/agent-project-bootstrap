#!/usr/bin/env python3
"""
parse_coverage.py — Parse test coverage reports from common formats.

Auto-detects format from filename + content. Emits a normalized JSON shape so
the audit script's Quality/Rework metric can compute coverage deltas across
windows.

Supported formats:
  - Istanbul / nyc / vitest `coverage-summary.json`
  - LCOV `lcov.info` (text)
  - Cobertura `coverage.xml` (used by pytest-cov, jacoco)
  - Python coverage.py `.coverage` is binary — not supported; use `coverage xml`

Usage:
  python3 parse_coverage.py <coverage-file> [--baseline <prior-file>]

Read-only. Touches nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_istanbul_summary(path: Path) -> dict | None:
    """Istanbul-format coverage-summary.json. Shape: {"total": {"lines": {"pct": ...}, ...}}"""
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    total = data.get("total") if isinstance(data, dict) else None
    if not isinstance(total, dict):
        return None

    def pct(key: str) -> float | None:
        block = total.get(key)
        if isinstance(block, dict):
            return block.get("pct")
        return None

    return {
        "format": "istanbul",
        "source_file": str(path),
        "lines_pct": pct("lines"),
        "branches_pct": pct("branches"),
        "functions_pct": pct("functions"),
        "statements_pct": pct("statements"),
    }


def parse_lcov(path: Path) -> dict | None:
    """LCOV info file. Each record block has LF / LH lines we sum."""
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    # LF = lines found; LH = lines hit. Same for BRF/BRH (branches), FNF/FNH (functions).
    sum_LF = sum_LH = sum_BRF = sum_BRH = sum_FNF = sum_FNH = 0
    saw_lcov_marker = False
    for line in text.splitlines():
        if line.startswith(("TN:", "SF:", "end_of_record")):
            saw_lcov_marker = True
        if line.startswith("LF:"):
            try: sum_LF += int(line[3:])
            except ValueError: pass
        elif line.startswith("LH:"):
            try: sum_LH += int(line[3:])
            except ValueError: pass
        elif line.startswith("BRF:"):
            try: sum_BRF += int(line[4:])
            except ValueError: pass
        elif line.startswith("BRH:"):
            try: sum_BRH += int(line[4:])
            except ValueError: pass
        elif line.startswith("FNF:"):
            try: sum_FNF += int(line[4:])
            except ValueError: pass
        elif line.startswith("FNH:"):
            try: sum_FNH += int(line[4:])
            except ValueError: pass
    if not saw_lcov_marker:
        return None

    def pct(hit: int, found: int) -> float | None:
        return (100.0 * hit / found) if found > 0 else None

    return {
        "format": "lcov",
        "source_file": str(path),
        "lines_pct": pct(sum_LH, sum_LF),
        "branches_pct": pct(sum_BRH, sum_BRF),
        "functions_pct": pct(sum_FNH, sum_FNF),
        "statements_pct": None,  # LCOV doesn't separate statements
    }


def parse_cobertura(path: Path) -> dict | None:
    """Cobertura XML: top-level <coverage line-rate=... branch-rate=...>"""
    try:
        tree = ET.parse(str(path))
    except (ET.ParseError, OSError):
        return None
    root = tree.getroot()
    if root.tag != "coverage":
        return None

    def pct(attr: str) -> float | None:
        v = root.get(attr)
        if v is None:
            return None
        try:
            return float(v) * 100.0  # cobertura rates are 0..1
        except ValueError:
            return None

    return {
        "format": "cobertura",
        "source_file": str(path),
        "lines_pct": pct("line-rate"),
        "branches_pct": pct("branch-rate"),
        "functions_pct": None,  # cobertura aggregates differently
        "statements_pct": None,
    }


# --- detection -----------------------------------------------------------

def detect_and_parse(path: Path) -> dict | None:
    if not path.exists():
        return None
    if path.suffix == ".json":
        return parse_istanbul_summary(path)
    if path.suffix == ".info":
        return parse_lcov(path)
    if path.suffix == ".xml":
        return parse_cobertura(path)
    # Fallback: read first bytes and guess
    try:
        head = path.read_bytes()[:200]
    except OSError:
        return None
    if head.startswith(b"<?xml") and b"<coverage" in head:
        return parse_cobertura(path)
    if head.startswith(b"{"):
        return parse_istanbul_summary(path)
    if b"LF:" in head or b"SF:" in head or b"TN:" in head:
        return parse_lcov(path)
    return None


# --- delta ---------------------------------------------------------------

def compute_delta(curr: dict, baseline: dict) -> dict:
    delta = {}
    for k in ("lines_pct", "branches_pct", "functions_pct", "statements_pct"):
        c = curr.get(k); b = baseline.get(k)
        if isinstance(c, (int, float)) and isinstance(b, (int, float)):
            delta[k] = round(c - b, 2)
        else:
            delta[k] = None
    return delta


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("coverage_file", type=Path)
    ap.add_argument("--baseline", type=Path, default=None,
                    help="Optional prior coverage file for delta computation")
    args = ap.parse_args(argv[1:])

    curr = detect_and_parse(args.coverage_file)
    if curr is None:
        print(json.dumps({
            "error": "could not detect or parse coverage file",
            "path": str(args.coverage_file),
            "supported_formats": ["istanbul-json", "lcov", "cobertura-xml"],
        }), file=sys.stderr)
        return 1

    out = {"current": curr}
    if args.baseline:
        baseline = detect_and_parse(args.baseline)
        if baseline is None:
            out["baseline_error"] = f"could not parse baseline: {args.baseline}"
        else:
            out["baseline"] = baseline
            out["delta"] = compute_delta(curr, baseline)

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
