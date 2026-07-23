"""M3 — ``baron finding new`` / ``baron decision new``: race-safe ledger appends.

ID allocation is push-retry based (ADR-003): parse the index for the max ID
(both heading ``### F<N>`` and table-row ``| F<N> |`` forms — real indexes carry
both), append a house-style stub, commit, push. If the push is rejected
(someone else claimed the number first — the F38/F39, F40/F41, F44/F45 collision
class), roll our commit back, rebase onto origin, re-parse, renumber, retry
(bounded). git's push atomicity is the lock; no extra store, no LOCK files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import clock
from .gitutil import GitError, git, has_remote, is_git_repo


class LedgerError(RuntimeError):
    """A ledger operation could not be completed."""


@dataclass(frozen=True)
class LedgerKind:
    name: str  # "finding" | "decision"
    prefix: str  # "F" | "D"
    index: str  # repo-relative index path


KINDS: dict[str, LedgerKind] = {
    "finding": LedgerKind("finding", "F", "findings/index.md"),
    "decision": LedgerKind("decision", "D", "decisions/index.md"),
}


def _patterns(prefix: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    return (
        re.compile(rf"^###\s+{prefix}(\d+)\b"),
        re.compile(rf"^\|\s*{prefix}(\d+)\s*\|"),
    )


def scan_ids(text: str, prefix: str) -> list[int]:
    """All IDs claimed in the index, in file order (headings + table rows)."""
    head_re, row_re = _patterns(prefix)
    ids: list[int] = []
    for line in text.splitlines():
        m = head_re.match(line) or row_re.match(line)
        if m:
            ids.append(int(m.group(1)))
    return ids


def next_id(text: str, prefix: str) -> int:
    return max(scan_ids(text, prefix), default=0) + 1


def render_entry(kind: LedgerKind, n: int, title: str, author: str, body: str) -> str:
    date = clock.today().isoformat()
    return f"### {kind.prefix}{n} — {title} ({date}, {author})\n\n{body.rstrip()}\n"


DEFAULT_BODY = "_Stub created by `baron {name} new`; expand with evidence or link the handoff._"


def add_entry(
    collab: Path,
    kind_name: str,
    *,
    title: str,
    author: str,
    body: str | None = None,
    push: bool = True,
    retries: int = 3,
) -> int:
    """Append a new entry, commit, and (unless ``push`` is false) push with the
    bounded fetch-rebase-renumber retry loop. Returns the allocated ID."""
    kind = KINDS[kind_name]
    index_path = collab / kind.index
    if not index_path.is_file():
        raise LedgerError(f"{index_path} not found — run from a collab repo (or --collab)")
    if not is_git_repo(collab):
        raise LedgerError(f"{collab} is not a git repository")
    if push and not has_remote(collab):
        raise LedgerError(f"{collab} has no origin remote — use --no-push")

    entry_body = body if body is not None else DEFAULT_BODY.format(name=kind.name)
    attempts = 1 + max(retries, 0)
    for attempt in range(attempts):
        text = index_path.read_text(encoding="utf-8")
        n = next_id(text, kind.prefix)
        entry = render_entry(kind, n, title, author, entry_body)
        index_path.write_text(text.rstrip("\n") + "\n\n" + entry, encoding="utf-8")

        slug_author = author.strip().split()[0].lower() if author.strip() else "baron"
        message = f"{slug_author}: ledger | {kind.prefix}{n} — {title}"
        git(collab, "add", "--", kind.index)
        git(collab, "commit", "-m", message, "--", kind.index)

        if not push:
            return n
        pushed = git(collab, "push", "origin", "HEAD", check=False)
        if pushed.returncode == 0:
            return n

        # Push rejected: someone else claimed the number. Drop our commit,
        # sync with origin, and re-run allocation against the fresh index.
        git(collab, "reset", "--hard", "HEAD~1")
        pulled = git(collab, "pull", "--rebase", check=False)
        if pulled.returncode != 0:
            raise GitError(
                f"push rejected and `git pull --rebase` failed in {collab}: "
                f"{pulled.stderr.strip()}"
            )
    raise LedgerError(
        f"push still rejected after {retries} retries — origin is moving too fast; "
        "re-run, or use --no-push and reconcile manually"
    )
