"""M5 — ``baron lock claim|release|list``: PR-as-lock, mechanized.

ADR-002 §3 replaced markdown LOCK commits (race-prone: two personas grep, both
see no lock, both claim) with lock-via-open-PR: **the open PR is the lock** —
claim = a draft PR labeled ``lock:<path>`` from a ``lock/<slug>`` branch with
one empty commit; release = close the PR + delete the branch; the forge's PR
list is the single query surface. A CI guard template
(``.github/workflows/lock-guard.yml`` in the emitted collab-repo assets) fails
any other PR touching a locked path.

All forge calls go through the :class:`~baron.forge.base.Forge` Protocol so
tests inject a fake and no ``gh`` is needed off the happy path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import clock, gitutil
from .forge import Forge, get_forge

LOCK_LABEL_PREFIX = "lock:"
LOCK_BRANCH_PREFIX = "lock/"


class LockError(RuntimeError):
    """A lock operation could not be completed."""


def _slugify(path: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return slug or "path"


def lock_label(path: str) -> str:
    return f"{LOCK_LABEL_PREFIX}{path}"


def lock_branch(path: str) -> str:
    return f"{LOCK_BRANCH_PREFIX}{_slugify(path)}"


@dataclass(frozen=True)
class Lock:
    path: str
    holder: str
    pr_number: int
    age_days: int | None
    branch: str
    url: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "holder": self.holder,
            "pr": self.pr_number,
            "age_days": self.age_days,
            "branch": self.branch,
            "url": self.url,
        }


def _label_names(pr: dict) -> list[str]:
    """gh returns labels as [{"name": ...}]; fakes may use plain strings."""
    out: list[str] = []
    for label in pr.get("labels") or []:
        if isinstance(label, dict):
            out.append(str(label.get("name", "")))
        else:
            out.append(str(label))
    return out


def _holder(pr: dict) -> str:
    author = pr.get("author")
    if isinstance(author, dict):
        return str(author.get("login") or "?")
    return str(author or "?")


def _age_days(pr: dict) -> int | None:
    created = pr.get("createdAt")
    if not created:
        return None
    try:
        dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (clock.now() - dt).days


def _as_lock(pr: dict, label: str) -> Lock:
    return Lock(
        path=label[len(LOCK_LABEL_PREFIX) :],
        holder=_holder(pr),
        pr_number=int(pr.get("number", 0)),
        age_days=_age_days(pr),
        branch=str(pr.get("headRefName", "")),
        url=str(pr.get("url", "")),
    )


def _open_locks(repo: Path, forge: Forge) -> list[Lock]:
    out: list[Lock] = []
    for pr in forge.list_open_prs(repo):
        for label in _label_names(pr):
            if label.startswith(LOCK_LABEL_PREFIX):
                out.append(_as_lock(pr, label))
    return out


def claim(
    repo: Path, path: str, *, reason: str | None = None, forge: Forge | None = None
) -> str:
    """Claim ``path``: lock/<slug> branch + empty commit + draft PR labeled
    ``lock:<path>``. Refuses (naming the holder) if an open lock PR for the
    same path already exists. Returns the lock PR's URL."""
    forge = forge if forge is not None else get_forge()
    existing = [l for l in _open_locks(repo, forge) if l.path == path]
    if existing:
        holder = existing[0]
        raise LockError(
            f"{path} is already locked by {holder.holder} "
            f"(PR #{holder.pr_number}, {holder.url or holder.branch}) — "
            "wait for release, or coordinate via _handoff/"
        )
    base = forge.default_branch(repo) or gitutil.default_branch(repo) or "main"
    branch = lock_branch(path)
    forge.create_branch(
        repo, branch=branch, base=base, message=f"lock: claim {path}"
    )
    body_lines = [
        f"**Lock claim** for `{path}` (PR-as-lock, COORDINATION.md lock mechanics).",
        "",
        f"- Reason: {reason or '(none given)'}",
        f"- Release: `baron lock release {path}` (or merge/close this PR).",
        "",
        "This PR carries one empty commit; it exists only to hold the lock.",
    ]
    return forge.open_pr(
        repo,
        title=f"lock: {path}",
        body="\n".join(body_lines),
        base=base,
        draft=True,
        head=branch,
        labels=[lock_label(path)],
    )


def release(repo: Path, path: str, *, forge: Forge | None = None) -> int:
    """Release the lock on ``path``: close its lock PR + delete the branch.
    Returns the closed PR number."""
    forge = forge if forge is not None else get_forge()
    matches = [l for l in _open_locks(repo, forge) if l.path == path]
    if not matches:
        raise LockError(f"no open lock PR found for {path} — nothing to release")
    held = matches[0]
    forge.close_pr(repo, held.pr_number, delete_branch=True)
    return held.pr_number


def list_locks(repo: Path, *, forge: Forge | None = None) -> list[Lock]:
    """All open locks (every open PR carrying a ``lock:*`` label)."""
    forge = forge if forge is not None else get_forge()
    return sorted(_open_locks(repo, forge), key=lambda l: l.path)


def render_table(locks: list[Lock]) -> str:
    if not locks:
        return "no open locks"
    rows = [("PATH", "HOLDER", "AGE", "PR")]
    for l in locks:
        age = f"{l.age_days}d" if l.age_days is not None else "?"
        rows.append((l.path, l.holder, age, f"#{l.pr_number}"))
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    return "\n".join(
        "  ".join(r[i].ljust(widths[i]) for i in range(3)) + "  " + r[3] for r in rows
    )
