"""M6-tooling acceptance: worktree topology.

Builds a real repo, adds two persona worktrees, commits in one, and asserts:
``worktree list`` shows the divergence, ``baron status`` reports the worktree's
divergence via the manifest's ``workspace.worktrees_root`` (the same sweep as
clones), and ``worktree remove`` refuses on unmerged commits until --force.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from typer.testing import CliRunner

from baron import worktree
from baron.cli import app

from conftest import clone, commit_file, init_bare, init_repo, run_git

runner = CliRunner()


@pytest.fixture
def code_repo(tmp_path: Path) -> Path:
    origin = init_bare(tmp_path / "origin.git")
    repo = clone(origin, tmp_path / "code")
    commit_file(repo, "src/app.py", "print('v1')\n", "seed: initial")
    run_git(repo, "push", "-q", "-u", "origin", "main")
    return repo


def test_add_two_personas_and_list(code_repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "worktrees"
    a = worktree.add(code_repo, "fern", root)
    b = worktree.add(code_repo, "moss", root)
    assert a == root / "fern" and a.is_dir()
    assert b == root / "moss" and b.is_dir()

    worktrees = worktree.list_worktrees(code_repo)
    assert [w.branch for w in worktrees] == ["main", "persona/fern", "persona/moss"]
    assert worktrees[0].is_main
    assert all(w.ahead == 0 and w.behind == 0 for w in worktrees)

    # Commit in fern's worktree: its branch is now ahead of origin/main.
    commit_file(a, "src/fern.py", "print('fern')\n", "fern: work")
    worktrees = worktree.list_worktrees(code_repo)
    fern = next(w for w in worktrees if w.branch == "persona/fern")
    moss = next(w for w in worktrees if w.branch == "persona/moss")
    assert fern.ahead == 1 and fern.behind == 0
    assert moss.ahead == 0


def test_add_refuses_existing_path_and_reuses_existing_branch(
    code_repo: Path, tmp_path: Path
) -> None:
    root = tmp_path / "worktrees"
    worktree.add(code_repo, "fern", root)
    with pytest.raises(worktree.WorktreeError, match="already exists"):
        worktree.add(code_repo, "fern", root)
    # Removing and re-adding reuses the surviving persona/fern branch.
    worktree.remove(code_repo, "fern")
    dest = worktree.add(code_repo, "fern", root)
    assert dest.is_dir()


def test_remove_refuses_unmerged_then_succeeds_with_force(
    code_repo: Path, tmp_path: Path
) -> None:
    root = tmp_path / "worktrees"
    wt = worktree.add(code_repo, "fern", root)
    commit_file(wt, "src/fern.py", "print('fern')\n", "fern: unmerged work")
    with pytest.raises(worktree.WorktreeError, match="not merged"):
        worktree.remove(code_repo, "fern")
    removed = worktree.remove(code_repo, "fern", force=True)
    assert removed == wt
    assert not wt.exists()
    # The branch (and its commits) survive — removing a worktree never deletes history.
    out = run_git(code_repo, "rev-list", "--count", "origin/main..persona/fern")
    assert out.strip() == "1"


def test_remove_refuses_dirty_worktree(code_repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "worktrees"
    wt = worktree.add(code_repo, "fern", root)
    (wt / "scratch.txt").write_text("uncommitted\n", encoding="utf-8")
    with pytest.raises(worktree.WorktreeError, match="uncommitted"):
        worktree.remove(code_repo, "fern")
    worktree.remove(code_repo, "fern", force=True)


def test_status_reports_worktree_divergence_via_manifest(
    code_repo: Path, tmp_path: Path, fixed_clock: object
) -> None:
    root = tmp_path / "worktrees"
    fern = worktree.add(code_repo, "fern", root)
    worktree.add(code_repo, "moss", root)
    commit_file(fern, "src/fern.py", "print('fern')\n", "fern: unpushed work")

    collab = init_repo(tmp_path / "collab")
    (collab / "manifest.yaml").write_text(
        f"""\
project: {{name: wt-test, description: worktree sweep}}
paths: {{strategy: relative, root: .}}
repos:
  - {{id: code, path: ../code, role: code, remote: unused}}
  - {{id: collab, path: ., role: collab}}
backlog: {{source: file, location: backlog.md}}
personas:
  - {{slug: fern, spec: agents/fern/persona.yaml}}
workspace:
  worktrees_root: ../worktrees
""",
        encoding="utf-8",
    )
    run_git(collab, "add", "-A")
    run_git(collab, "commit", "-q", "-m", "collab: bootstrap")

    result = runner.invoke(app, ["status", "--collab", str(collab), "--json"])
    assert result.exit_code == 1, result.output
    findings = json.loads(result.output)["findings"]
    ahead = [
        f for f in findings if f["check"] == "ahead" and "worktree:fern" in f["subject"]
    ]
    assert ahead, findings
    # moss is clean: no red findings against it.
    assert not [
        f
        for f in findings
        if "worktree:moss" in f["subject"] and f["severity"] == "red"
    ], findings


def test_worktree_cli_add_list_remove(code_repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "worktrees"
    result = runner.invoke(
        app,
        ["worktree", "add", "fern", "--repo", str(code_repo), "--root", str(root)],
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["worktree", "list", "--repo", str(code_repo)])
    assert result.exit_code == 0, result.output
    assert "persona/fern" in result.output
    result = runner.invoke(
        app, ["worktree", "remove", "fern", "--repo", str(code_repo)]
    )
    assert result.exit_code == 0, result.output
    assert "branch persona/fern kept" in result.output
