"""Status waivers — ``.baron-waivers.yaml`` + ``baron waiver add|list``.

Surfaced by the first pilot triage (2026-07-23, docs/BACKLOG.md): some red
``baron status`` findings are deliberate (e.g. a branch parked for a future
experiment) and should not stay red forever — but silently ignoring them
would rot. A waiver downgrades matching red findings to warn, always showing
the reason; **expiry keeps waivers honest** — an expired waiver stops
matching (the red resurfaces) and is itself reported as a warn.

File format (collab-repo root, human-legible YAML — the substrate rule,
ADR-003 §2.2):

.. code-block:: yaml

    waivers:
      - subject: "clone:rex *"            # fnmatch pattern on the SUBJECT column
        reason: kept for the vNext experiment
        handoff: _handoff/2026-07-23-parked-branch.md
        expires: 2026-08-15               # YYYY-MM-DD

The file is baron-managed when written via ``baron waiver add`` (a full
rewrite in a canonical shape; the ``reason`` field is where prose belongs).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fnmatch import fnmatch
from pathlib import Path

import yaml

from . import clock
from .frontmatter import as_date

WAIVERS_FILE = ".baron-waivers.yaml"

_HEADER = (
    "# baron status waivers — see `baron waiver --help`.\n"
    "# A waiver downgrades red findings whose SUBJECT matches `subject`\n"
    "# (fnmatch) to warn, until `expires`. Expired waivers are ignored and\n"
    "# reported as their own warn. Managed by `baron waiver add`.\n"
)


class WaiverError(RuntimeError):
    """A waiver operation could not be completed."""


@dataclass(frozen=True)
class Waiver:
    subject: str  # fnmatch pattern on the status SUBJECT column
    reason: str
    handoff: str  # collab-relative path of the handoff explaining the park
    expires: date

    def expired(self, today: date) -> bool:
        return today > self.expires

    def matches(self, subject: str) -> bool:
        return fnmatch(subject, self.subject)

    def to_dict(self) -> dict[str, str]:
        return {
            "subject": self.subject,
            "reason": self.reason,
            "handoff": self.handoff,
            "expires": self.expires.isoformat(),
        }


def load(collab: Path) -> tuple[list[Waiver], list[str]]:
    """(waivers, problems). Malformed entries become problem strings, never
    silent drops — a waiver that doesn't parse must not hide a red."""
    path = collab / WAIVERS_FILE
    if not path.is_file():
        return [], []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [], [f"{WAIVERS_FILE} does not parse: {exc}"]
    if data is None:
        return [], []
    entries = data.get("waivers") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        return [], [f"{WAIVERS_FILE}: expected a `waivers:` list"]
    waivers: list[Waiver] = []
    problems: list[str] = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            problems.append(f"{WAIVERS_FILE} entry {i + 1}: not a mapping")
            continue
        subject = str(entry.get("subject") or "").strip()
        expires = as_date(entry.get("expires"))
        if not subject or expires is None:
            problems.append(
                f"{WAIVERS_FILE} entry {i + 1}: needs `subject` and a "
                "YYYY-MM-DD `expires`"
            )
            continue
        waivers.append(
            Waiver(
                subject=subject,
                reason=str(entry.get("reason") or "(no reason recorded)").strip(),
                handoff=str(entry.get("handoff") or "?").strip(),
                expires=expires,
            )
        )
    return waivers, problems


def render_file(waivers: list[Waiver]) -> str:
    # yaml.safe_dump, not hand-rolled lines: a reason like "Routed: rebase #98"
    # contains a mapping colon and a comment marker, both of which broke the
    # first hand-rolled version of this writer (found live, 2026-07-23).
    body = yaml.safe_dump(
        {"waivers": [w.to_dict() for w in waivers]},
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=88,
    )
    return _HEADER + "\n" + body


def add(
    collab: Path, subject: str, *, reason: str, handoff: str, expires: str
) -> Path:
    """Append a waiver (canonical rewrite of the managed file)."""
    expiry = as_date(expires)
    if expiry is None:
        raise WaiverError(f"--expires must be YYYY-MM-DD, got {expires!r}")
    if expiry < clock.today():
        raise WaiverError(f"--expires {expiry} is already in the past")
    existing, problems = load(collab)
    if problems:
        raise WaiverError(
            "existing waivers file has problems, fix it first: " + "; ".join(problems)
        )
    if any(w.subject == subject for w in existing):
        raise WaiverError(f"a waiver for subject pattern {subject!r} already exists")
    existing.append(
        Waiver(subject=subject, reason=reason, handoff=handoff, expires=expiry)
    )
    path = collab / WAIVERS_FILE
    path.write_text(render_file(existing), encoding="utf-8")
    return path
