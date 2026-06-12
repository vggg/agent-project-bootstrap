#!/usr/bin/env python3
"""
compute_centrality.py — Betweenness centrality on the coordination network.

Builds a multi-edge graph from the audit's coordination signals (handoffs +
PR reviews + merges), computes betweenness centrality for each actor, and
identifies single-point-of-failure (SPOF) candidates per the audit heuristic
(top centrality > 2.5x mean → flag).

Stdlib-only implementation of Brandes' algorithm.

Usage:
  python3 compute_centrality.py --handoffs-dir <vault>/_handoff [other inputs] \\
    [--reviews-json <file>] [--merges-json <file>] [--format json|md]

The --handoffs-dir scans markdown files for `from:` / `for:` frontmatter.
Optional JSON inputs let you supply pre-extracted PR review and merge data
(see schemas in the source).

Read-only. Touches nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path


SPOF_THRESHOLD = 2.5  # top / mean centrality ratio above which we flag SPOF


def parse_handoffs(handoffs_dir: Path) -> list[tuple[str, str]]:
    """Return list of (from_actor, for_actor) edges from handoff markdown files."""
    edges = []
    for p in sorted(handoffs_dir.glob("*.md")):
        try:
            text = p.read_text(errors="replace")[:2000]  # frontmatter is at top
        except Exception:
            continue
        fr = re.search(r"^from:\s*(.+?)\s*$", text, re.MULTILINE | re.IGNORECASE)
        fo = re.search(r"^for:\s*(.+?)\s*$", text, re.MULTILINE | re.IGNORECASE)
        if fr and fo:
            from_actor = fr.group(1).strip().lower()
            for_actor = fo.group(1).strip().lower()
            # Special case: for: all → emit one edge to "all" (treated as a node)
            edges.append((from_actor, for_actor))
    return edges


def parse_reviews_json(path: Path) -> list[tuple[str, str]]:
    """Parse a reviews JSON of shape [{reviewer, author, pr}, ...]."""
    if not path or not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return []
    return [(r["reviewer"].lower(), r["author"].lower()) for r in data if "reviewer" in r and "author" in r]


def parse_merges_json(path: Path) -> list[tuple[str, str]]:
    """Parse a merges JSON of shape [{merger, author, pr}, ...]."""
    if not path or not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return []
    return [(m["merger"].lower(), m["author"].lower()) for m in data if "merger" in m and "author" in m]


def build_graph(edges: list[tuple[str, str]]) -> tuple[set[str], dict[str, set[str]]]:
    """Build an undirected adjacency dict + node set from a list of edges.

    Treats the graph as undirected for centrality (information flows both ways
    in coordination). Multi-edges collapse to single edge for shortest-path math
    but contribute to edge weights (we keep weight 1 for simplicity in this v1).
    """
    nodes: set[str] = set()
    adj: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        if a == b:
            continue
        nodes.add(a); nodes.add(b)
        adj[a].add(b); adj[b].add(a)
    return nodes, adj


def betweenness_centrality(nodes: set[str], adj: dict[str, set[str]]) -> dict[str, float]:
    """Brandes' algorithm. O(V*E) for unweighted graphs."""
    cb = {v: 0.0 for v in nodes}
    for s in nodes:
        # BFS from s
        S: list[str] = []
        P: dict[str, list[str]] = {v: [] for v in nodes}
        sigma: dict[str, float] = {v: 0.0 for v in nodes}
        sigma[s] = 1.0
        d: dict[str, int] = {v: -1 for v in nodes}
        d[s] = 0
        Q: deque[str] = deque([s])
        while Q:
            v = Q.popleft()
            S.append(v)
            for w in adj.get(v, ()):
                if d[w] < 0:
                    d[w] = d[v] + 1
                    Q.append(w)
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]
                    P[w].append(v)
        delta: dict[str, float] = {v: 0.0 for v in nodes}
        while S:
            w = S.pop()
            for v in P[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]
    # For undirected, divide by 2 (each shortest path counted twice)
    return {v: cb[v] / 2.0 for v in nodes}


def render_json(centrality: dict[str, float], edges_count: dict[str, int], spof: dict) -> str:
    sorted_actors = sorted(centrality.items(), key=lambda kv: -kv[1])
    return json.dumps({
        "actors": [
            {"actor": a, "centrality": round(c, 4), "rank": i + 1}
            for i, (a, c) in enumerate(sorted_actors)
        ],
        "edges_by_type": edges_count,
        "spof": spof,
    }, indent=2)


def render_md(centrality: dict[str, float], edges_count: dict[str, int], spof: dict) -> str:
    sorted_actors = sorted(centrality.items(), key=lambda kv: -kv[1])
    lines = [
        "### Coordination network centrality",
        "",
        f"Edges by type: " + ", ".join(f"{k} {v}" for k, v in edges_count.items()),
        "",
        "| Rank | Actor | Betweenness centrality |",
        "|---|---|---|",
    ]
    for i, (a, c) in enumerate(sorted_actors[:15]):
        lines.append(f"| {i+1} | {a} | {c:.4f} |")
    if spof.get("flagged"):
        lines += [
            "",
            f"⚠️ **SPOF flagged:** `{spof['top_actor']}` — centrality {spof['top_centrality']:.4f} is {spof['ratio']:.2f}× the mean ({spof['mean']:.4f}); above the {SPOF_THRESHOLD}× threshold.",
        ]
    else:
        lines += [
            "",
            f"No SPOF threshold breach. Top actor `{spof['top_actor']}` is {spof['ratio']:.2f}× the mean (threshold: {SPOF_THRESHOLD}×).",
        ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--handoffs-dir", type=Path, default=None)
    ap.add_argument("--reviews-json", type=Path, default=None)
    ap.add_argument("--merges-json", type=Path, default=None)
    ap.add_argument("--format", choices=("md", "json"), default="md")
    args = ap.parse_args(argv[1:])

    edges = []
    edges_count: dict[str, int] = {}

    if args.handoffs_dir and args.handoffs_dir.exists():
        h_edges = parse_handoffs(args.handoffs_dir)
        edges += h_edges
        edges_count["handoff"] = len(h_edges)
    if args.reviews_json:
        r_edges = parse_reviews_json(args.reviews_json)
        edges += r_edges
        edges_count["review"] = len(r_edges)
    if args.merges_json:
        m_edges = parse_merges_json(args.merges_json)
        edges += m_edges
        edges_count["merge"] = len(m_edges)

    if not edges:
        print("error: no edges to compute centrality on (provide at least one of --handoffs-dir / --reviews-json / --merges-json with data)", file=sys.stderr)
        return 1

    nodes, adj = build_graph(edges)
    centrality = betweenness_centrality(nodes, adj)

    sorted_actors = sorted(centrality.items(), key=lambda kv: -kv[1])
    top_actor, top_c = sorted_actors[0]
    nonzero = [c for c in centrality.values() if c > 0] or [0.0]
    mean_c = sum(nonzero) / len(nonzero) if nonzero else 0.0
    ratio = (top_c / mean_c) if mean_c > 0 else 0.0
    spof = {
        "top_actor": top_actor,
        "top_centrality": top_c,
        "mean": mean_c,
        "ratio": ratio,
        "threshold": SPOF_THRESHOLD,
        "flagged": ratio > SPOF_THRESHOLD,
    }

    if args.format == "json":
        print(render_json(centrality, edges_count, spof))
    else:
        print(render_md(centrality, edges_count, spof))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
