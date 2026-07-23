"""CLI-surface smoke tests: help text, subcommand wiring, index exit codes, forge."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from baron.cli import app
from baron.forge import ForgeError, ForgeUnavailable, GitHubForge, get_forge

from conftest import init_repo, run_git

runner = CliRunner()


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["validate", "--help"],
        ["status", "--help"],
        ["finding", "new", "--help"],
        ["decision", "new", "--help"],
        ["handoff", "create", "--help"],
        ["handoff", "close", "--help"],
        ["handoff", "list", "--help"],
        ["index", "--help"],
    ],
)
def test_help_surfaces(args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "--help" in result.output or "Usage" in result.output


def test_index_command_flags_duplicates(tmp_path: Path, fixed_clock: object) -> None:
    collab = init_repo(tmp_path / "collab")
    (collab / "findings").mkdir()
    (collab / "findings" / "index.md").write_text(
        "### F7 — a (2026-07-01, X)\n\n### F7 — b (2026-07-02, Y)\n", encoding="utf-8"
    )
    run_git(collab, "add", "-A")
    run_git(collab, "commit", "-q", "-m", "x")
    result = runner.invoke(app, ["index", "--collab", str(collab)])
    assert result.exit_code == 1
    assert "duplicate" in result.output
    assert (collab / "_handoff" / "README.md").is_file()


def test_get_forge_github_builtin() -> None:
    forge = get_forge("github")
    assert isinstance(forge, GitHubForge)
    assert isinstance(forge.available(), bool)


def test_get_forge_unknown_mentions_plugin_group() -> None:
    with pytest.raises(ForgeError, match="baron.forges"):
        get_forge("gitlab")  # backlog: ships as a plugin, see docs/BACKLOG.md


def test_github_forge_unavailable_without_gh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))  # no gh here
    forge = GitHubForge()
    assert forge.available() is False
    with pytest.raises(ForgeUnavailable, match="gh"):
        forge.list_open_prs(tmp_path)
