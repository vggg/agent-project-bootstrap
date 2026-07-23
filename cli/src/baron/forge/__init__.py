"""Forge abstraction — pluggable code-hosting backends.

GitHub ships built-in (via the ``gh`` CLI, an accepted prerequisite for forge
features only — everything in M1–M3 works without it). Other forges arrive as
plugins through the ``baron.forges`` entry-point group (see docs/BACKLOG.md for
the GitLab design sketch): a plugin distribution registers

    [project.entry-points."baron.forges"]
    gitlab = "baron_gitlab:GitLabForge"

and a manifest selects it with ``forge: gitlab``.
"""

from __future__ import annotations

from importlib.metadata import entry_points

from .base import Forge, ForgeError, ForgeUnavailable
from .github import GitHubForge

__all__ = ["Forge", "ForgeError", "ForgeUnavailable", "GitHubForge", "get_forge"]

_BUILTIN: dict[str, type] = {"github": GitHubForge}


def get_forge(name: str = "github") -> Forge:
    """Resolve a forge by name: built-ins first, then ``baron.forges`` plugins."""
    if name in _BUILTIN:
        return _BUILTIN[name]()
    for ep in entry_points(group="baron.forges"):
        if ep.name == name:
            forge_cls = ep.load()
            return forge_cls()
    raise ForgeError(
        f"no forge named {name!r} — built-ins: {sorted(_BUILTIN)}; "
        "plugins register under the 'baron.forges' entry-point group"
    )
