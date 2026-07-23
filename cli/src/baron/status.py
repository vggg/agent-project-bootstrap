"""M2 — ``baron status``: divergence & staleness report over a collab-repo project.

Reads ``manifest.yaml`` for the repo/persona topology (plus the optional v1.2
``workspace.clones`` / ``workspace.worktrees_root`` fields) and reports, with
severity:

- red — commits ahead of origin (unpushed), behind origin (never pulled),
  local branches unmerged to the origin default branch, open handoffs past SLA.
  These are exactly the three stranding classes from the 2026-07-22
  badminton-analyzer incident plus the handoff-rot signal (18/40 open).
- warn — uncommitted dirt, ledger staleness vs code-repo activity (an explicit
  HEURISTIC), wiki/status.md older than the newest finding.

Exit 0 = green (warnings allowed); exit 1 = at least one red finding (CI-usable).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import clock, gitutil
from .frontmatter import as_date, split_frontmatter

RED = "red"
WARN = "warn"

_LEDGER_LINE_RE = re.compile(r"^(?:###\s+[FD]\d+\b|\|\s*[FD]\d+\s*\|)")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


@dataclass
class StatusFinding:
    severity: str  # "red" | "warn"
    area: str  # "repo" | "branch" | "handoff" | "ledger" | "wiki"
    subject: str
    check: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def load_manifest(collab: Path) -> dict:
    manifest_path = collab / "manifest.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"no manifest.yaml in {collab} — not a collab repo?")
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{manifest_path}: manifest is not a mapping")
    return data


def _resolve_root(collab: Path, manifest: dict) -> Path:
    root = str(manifest.get("paths", {}).get("root", ".") or ".")
    return (collab / root).resolve()


def _targets(collab: Path, manifest: dict) -> list[tuple[str, Path]]:
    """(label, path) for every working copy the manifest describes."""
    root = _resolve_root(collab, manifest)
    out: list[tuple[str, Path]] = []
    for repo in manifest.get("repos", []) or []:
        if isinstance(repo, dict) and "path" in repo:
            out.append((f"repo:{repo.get('id', '?')}", (root / str(repo["path"])).resolve()))
    workspace = manifest.get("workspace") or {}
    for clone in workspace.get("clones", []) or []:
        if isinstance(clone, dict) and "path" in clone:
            label = f"clone:{clone.get('persona', '?')}"
            out.append((label, (root / str(clone["path"])).resolve()))
    worktrees_root = workspace.get("worktrees_root")
    if worktrees_root:
        wt_root = (root / str(worktrees_root)).resolve()
        if wt_root.is_dir():
            for child in sorted(wt_root.iterdir()):
                if (child / ".git").exists():
                    out.append((f"worktree:{child.name}", child))
    return out


def _check_working_copy(
    label: str, path: Path, fetch: bool, out: list[StatusFinding]
) -> None:
    subject = f"{label} {path}"
    if not path.is_dir():
        out.append(StatusFinding(RED, "repo", subject, "missing", "path does not exist"))
        return
    if not gitutil.is_git_repo(path):
        out.append(StatusFinding(RED, "repo", subject, "not-a-repo", "not a git working copy"))
        return

    dirt = gitutil.dirty_count(path)
    if dirt:
        out.append(
            StatusFinding(WARN, "repo", subject, "dirty", f"{dirt} uncommitted path(s)")
        )

    if not gitutil.has_remote(path):
        # Local-only repos are valid (manifest.schema.md); nothing to diverge from.
        return
    if fetch and not gitutil.fetch(path):
        out.append(StatusFinding(WARN, "repo", subject, "fetch-failed", "git fetch origin failed"))

    default = gitutil.default_branch(path)
    if default is None:
        out.append(
            StatusFinding(WARN, "repo", subject, "no-default-branch",
                          "cannot determine origin default branch (try --fetch)")
        )
        return
    upstream = f"origin/{default}"

    try:
        ahead, behind = gitutil.ahead_behind(path, upstream)
    except gitutil.GitError as exc:
        out.append(StatusFinding(WARN, "repo", subject, "compare-failed", str(exc)))
        return
    if ahead:
        out.append(
            StatusFinding(RED, "repo", subject, "ahead",
                          f"{ahead} commit(s) ahead of {upstream} (unpushed)")
        )
    if behind:
        out.append(
            StatusFinding(RED, "repo", subject, "behind",
                          f"{behind} commit(s) behind {upstream} (never pulled)")
        )

    today = clock.today()
    for branch, ts in gitutil.local_branches(path):
        if branch == default:
            continue  # HEAD-vs-upstream already covers the default branch
        try:
            unmerged = gitutil.commits_not_in(path, branch, upstream)
        except gitutil.GitError:
            continue
        if unmerged:
            last = datetime.fromtimestamp(ts, tz=timezone.utc).date() if ts else None
            age = (today - last).days if last is not None else "?"
            out.append(
                StatusFinding(
                    RED, "branch", f"{label} {branch}", "unmerged-branch",
                    f"{unmerged} commit(s) not merged to {upstream}; last commit {age}d ago",
                )
            )


def _check_handoffs(collab: Path, sla_days: int, out: list[StatusFinding]) -> None:
    handoff_dir = collab / "_handoff"
    if not handoff_dir.is_dir():
        return
    today = clock.today()
    for path in sorted(handoff_dir.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        if not meta or str(meta.get("status", "")).strip() != "open":
            continue
        created = as_date(meta.get("created"))
        if created is None:
            out.append(
                StatusFinding(WARN, "handoff", path.name, "no-created-date",
                              "open handoff has no parseable created: date")
            )
            continue
        age = (today - created).days
        if age > sla_days:
            out.append(
                StatusFinding(
                    RED, "handoff", path.name, "handoff-overdue",
                    f"open for {age}d (SLA {sla_days}d), for: {meta.get('for', '?')}",
                )
            )


def _max_ledger_date(collab: Path) -> str | None:
    """Newest ISO date on an F/D entry line in the ledgers. None if none found."""
    dates: list[str] = []
    for rel in ("findings/index.md", "decisions/index.md"):
        path = collab / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if _LEDGER_LINE_RE.match(line):
                dates.extend(_DATE_RE.findall(line))
    return max(dates) if dates else None


def _max_finding_date(collab: Path) -> str | None:
    path = collab / "findings/index.md"
    if not path.is_file():
        return None
    dates: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if _LEDGER_LINE_RE.match(line):
            dates.extend(_DATE_RE.findall(line))
    return max(dates) if dates else None


def _check_ledger_staleness(
    collab: Path, manifest: dict, out: list[StatusFinding]
) -> None:
    root = _resolve_root(collab, manifest)
    code_repos = [
        (root / str(r["path"])).resolve()
        for r in manifest.get("repos", []) or []
        if isinstance(r, dict) and r.get("role") == "code" and "path" in r
    ]
    ledger_max = _max_ledger_date(collab)
    if ledger_max is None:
        return
    for repo in code_repos:
        if not gitutil.is_git_repo(repo):
            continue
        code_date = gitutil.last_commit_date(repo, "docs", "src")
        if code_date and code_date > ledger_max:
            out.append(
                StatusFinding(
                    WARN, "ledger", "findings/decisions index", "ledger-stale",
                    f"newest ledger entry {ledger_max} < newest docs/src commit "
                    f"{code_date} in {repo.name} (HEURISTIC — commit dates vs entry dates)",
                )
            )


def _check_wiki(collab: Path, out: list[StatusFinding]) -> None:
    status_md = collab / "wiki" / "status.md"
    if not status_md.is_file():
        return
    meta, _ = split_frontmatter(status_md.read_text(encoding="utf-8"))
    updated = as_date((meta or {}).get("updated"))
    if updated is None:
        return
    newest_finding = _max_finding_date(collab)
    if newest_finding and newest_finding > updated.isoformat():
        out.append(
            StatusFinding(
                WARN, "wiki", "wiki/status.md", "wiki-stale",
                f"updated: {updated} < newest finding entry {newest_finding}",
            )
        )


def collect(collab: Path, *, fetch: bool = False, sla_days: int = 14) -> list[StatusFinding]:
    manifest = load_manifest(collab)
    out: list[StatusFinding] = []
    for label, path in _targets(collab, manifest):
        _check_working_copy(label, path, fetch, out)
    _check_handoffs(collab, sla_days, out)
    _check_ledger_staleness(collab, manifest, out)
    _check_wiki(collab, out)
    return out


def render_table(findings: list[StatusFinding]) -> str:
    if not findings:
        return "all green — no divergence, no overdue handoffs, ledgers current"
    rows = [("SEV", "AREA", "SUBJECT", "CHECK", "DETAIL")]
    rows += [(f.severity, f.area, f.subject, f.check, f.detail) for f in findings]
    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    lines = []
    for r in rows:
        lines.append(
            "  ".join(r[i].ljust(widths[i]) for i in range(4)) + "  " + r[4]
        )
    reds = sum(1 for f in findings if f.severity == RED)
    warns = len(findings) - reds
    lines.append(f"-- {reds} red, {warns} warn")
    return "\n".join(lines)
