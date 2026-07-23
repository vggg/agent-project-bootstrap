"""GitHub forge — implemented over the ``gh`` CLI via subprocess.

Stub scope (M1–M3): nothing in baron's shipped commands calls this yet; it
exists so the Protocol has one real implementation and so forge-consuming
milestones (and plugins) have the pattern to follow. ``gh`` is an accepted
prerequisite for forge features only — its absence raises
:class:`ForgeUnavailable` with an actionable message, and no M1–M3 path
requires it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .base import ForgeError, ForgeUnavailable


class GitHubForge:
    name = "github"

    def available(self) -> bool:
        return shutil.which("gh") is not None

    def _gh(self, repo: Path, *args: str) -> str:
        if not self.available():
            raise ForgeUnavailable(
                "GitHub CLI (`gh`) not found on PATH — install it for forge features; "
                "all of validate/status/finding/decision/handoff/index work without it"
            )
        proc = subprocess.run(
            ["gh", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise ForgeError(
                f"gh {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}"
            )
        return proc.stdout

    def default_branch(self, repo: Path) -> str | None:
        out = self._gh(
            repo, "repo", "view", "--json", "defaultBranchRef",
            "--jq", ".defaultBranchRef.name",
        ).strip()
        return out or None

    def open_pr(
        self,
        repo: Path,
        *,
        title: str,
        body: str,
        base: str | None = None,
        draft: bool = False,
    ) -> str:
        args = ["pr", "create", "--title", title, "--body", body]
        if base:
            args += ["--base", base]
        if draft:
            args.append("--draft")
        return self._gh(repo, *args).strip()

    def list_open_prs(self, repo: Path) -> list[dict[str, object]]:
        out = self._gh(
            repo, "pr", "list", "--state", "open",
            "--json", "number,title,headRefName",
        )
        loaded = json.loads(out or "[]")
        return loaded if isinstance(loaded, list) else []
