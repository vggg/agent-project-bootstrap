"""M2 acceptance: a synthetic divergent topology reproducing the three real
stranding classes from the badminton-analyzer 2026-07-22 incident (ADR-002/003):

1. a persona clone with commits never pushed (ahead of origin),
2. a persona clone with a pushed-but-unmerged branch,
3. the canonical clone behind origin (origin gained a commit it never pulled),

plus an overdue open handoff. `baron status --fetch` must flag all four in red
and exit 1.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from baron.cli import app

from conftest import clone, commit_file, init_bare, init_repo, run_git

runner = CliRunner()


def build_topology(tmp_path: Path) -> Path:
    """Returns the collab repo path."""
    origin = init_bare(tmp_path / "origin" / "code.git")

    seed = clone(origin, tmp_path / "seed")
    commit_file(seed, "src/app.py", "print('v1')\n", "seed: initial app")
    commit_file(seed, "docs/notes.md", "# notes\n", "seed: docs")
    run_git(seed, "push", "-q", "origin", "main")

    canonical = clone(origin, tmp_path / "canonical" / "code")
    tess = clone(origin, tmp_path / "clones" / "tess-code")
    rex = clone(origin, tmp_path / "clones" / "rex-code")

    # Stranding class 1: tess commits without pushing.
    commit_file(tess, "src/tess.py", "print('tess')\n", "tess: unpushed work")

    # Stranding class 2: rex pushes a branch that never merges to main.
    run_git(rex, "checkout", "-q", "-b", "rex/topic")
    commit_file(rex, "src/rex.py", "print('rex')\n", "rex: topic work")
    run_git(rex, "push", "-q", "origin", "rex/topic")
    run_git(rex, "checkout", "-q", "main")

    # Stranding class 3: origin gains a commit the canonical clone never pulls.
    drive_by = clone(origin, tmp_path / "drive-by")
    commit_file(drive_by, "src/app.py", "print('v2')\n", "cloud: hotfix on main")
    run_git(drive_by, "push", "-q", "origin", "main")

    # The collab repo (local-only git repo is valid per manifest.schema.md).
    collab = init_repo(tmp_path / "collab")
    (collab / "_handoff").mkdir()
    (collab / "_handoff" / "2026-06-15-overdue-ask.md").write_text(
        "---\n"
        "created: 2026-06-15\n"
        "status: open\n"
        "for: tess\n"
        "from: rex\n"
        "priority: high\n"
        "---\n\n# Overdue ask\n",
        encoding="utf-8",
    )
    (collab / "findings").mkdir()
    (collab / "findings" / "index.md").write_text(
        "# Findings — Index\n\n### F1 — First finding (2026-06-01, Tess)\n\nBody.\n",
        encoding="utf-8",
    )
    (collab / "manifest.yaml").write_text(
        """\
project:
  name: strand-test
  description: synthetic divergent topology
paths:
  strategy: relative
  root: .
repos:
  - id: code
    path: ../canonical/code
    role: code
    remote: unused
  - id: collab
    path: .
    role: collab
backlog:
  source: file
  location: backlog.md
personas:
  - slug: tess
    spec: agents/tess/persona.yaml
workspace:
  clones:
    - persona: tess
      path: ../clones/tess-code
    - persona: rex
      path: ../clones/rex-code
""",
        encoding="utf-8",
    )
    run_git(collab, "add", "-A")
    run_git(collab, "commit", "-q", "-m", "collab: bootstrap")
    return collab


def test_status_flags_all_three_stranding_classes_plus_overdue_handoff(
    tmp_path: Path, fixed_clock: object
) -> None:
    collab = build_topology(tmp_path)
    result = runner.invoke(
        app, ["status", "--collab", str(collab), "--fetch", "--sla", "14", "--json"]
    )
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    findings = payload["findings"]

    def reds(check: str) -> list[dict]:
        return [f for f in findings if f["check"] == check and f["severity"] == "red"]

    ahead = reds("ahead")
    assert any("tess" in f["subject"] for f in ahead), findings  # class 1
    unmerged = reds("unmerged-branch")
    assert any("rex/topic" in f["subject"] for f in unmerged), findings  # class 2
    behind = reds("behind")
    assert any("repo:code" in f["subject"] for f in behind), findings  # class 3
    overdue = reds("handoff-overdue")
    assert any("overdue-ask" in f["subject"] for f in overdue), findings

    # Ledger staleness heuristic: F1 dated 2026-06-01, code commits are today.
    assert any(f["check"] == "ledger-stale" and f["severity"] == "warn" for f in findings)


def test_status_green_topology_exits_zero(tmp_path: Path, fixed_clock: object) -> None:
    origin = init_bare(tmp_path / "origin.git")
    seed = clone(origin, tmp_path / "seed")
    commit_file(seed, "src/app.py", "print('v1')\n", "seed: initial")
    run_git(seed, "push", "-q", "origin", "main")
    canonical = clone(origin, tmp_path / "code")

    collab = init_repo(tmp_path / "collab")
    (collab / "manifest.yaml").write_text(
        """\
project: {name: green, description: all synced}
paths: {strategy: relative, root: .}
repos:
  - {id: code, path: ../code, role: code, remote: unused}
  - {id: collab, path: ., role: collab}
backlog: {source: file, location: backlog.md}
personas:
  - {slug: tess, spec: agents/tess/persona.yaml}
""",
        encoding="utf-8",
    )
    run_git(collab, "add", "-A")
    run_git(collab, "commit", "-q", "-m", "collab: bootstrap")
    assert canonical.is_dir()

    result = runner.invoke(app, ["status", "--collab", str(collab), "--fetch"])
    assert result.exit_code == 0, result.output
    assert "all green" in result.output


def test_status_human_table_lists_reds(tmp_path: Path, fixed_clock: object) -> None:
    collab = build_topology(tmp_path)
    result = runner.invoke(app, ["status", "--collab", str(collab), "--fetch"])
    assert result.exit_code == 1
    for token in ("ahead", "behind", "unmerged-branch", "handoff-overdue"):
        assert token in result.output, result.output
