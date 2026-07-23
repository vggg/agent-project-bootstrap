"""Minimal YAML-frontmatter helpers for _handoff/ and wiki/ files.

The files stay human-first: edits are textual (line-level) wherever possible so
`baron` never reflows prose a persona wrote.
"""

from __future__ import annotations

from datetime import date, datetime

import yaml


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter dict or None, body). Body includes everything after
    the closing ``---`` line. Malformed/absent frontmatter -> (None, text)."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            block = "".join(lines[1:i])
            try:
                meta = yaml.safe_load(block)
            except yaml.YAMLError:
                return None, text
            if not isinstance(meta, dict):
                return None, text
            return meta, "".join(lines[i + 1 :])
    return None, text


def as_date(value: object) -> date | None:
    """Coerce a frontmatter value (pyyaml date/datetime/str) to a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def render_frontmatter(meta: dict[str, object]) -> str:
    """Render a simple, ordered, human-legible frontmatter block."""
    lines = ["---"]
    for key, value in meta.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"
