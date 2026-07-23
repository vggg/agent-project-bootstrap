"""baron — command-line surface (typer app).

The markdown/git substrate is the database (ADR-003): every command below reads
and writes the same human-legible collab-repo files the personas do.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from . import clock, handoff as handoff_mod, indexer, ledger, status as status_mod, validate as validate_mod

app = typer.Typer(
    name="baron",
    help=(
        "Disciplined reader/writer over an agent-project-bootstrap collab repo. "
        "The markdown/git substrate is the database — baron never adds another store."
    ),
    no_args_is_help=True,
    add_completion=False,
)

_COLLAB_OPT = typer.Option(
    Path("."),
    "--collab",
    help="Path to the collab repo root (default: current directory).",
)


def _echo_json(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2, default=str))


# --- M1: validate ---------------------------------------------------------------------


@app.command()
def validate(
    path: Path = typer.Argument(
        Path("."),
        help="A persona.yaml/manifest.yaml file, or a directory to search recursively.",
    ),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Validate persona.yaml / manifest.yaml against the canonical v1 schemas.

    Checks: YAML parse, missing/unknown fields, types, capability verbs against
    the FROZEN v1 vocabulary, allow/deny overlap, unfilled {{PLACEHOLDER}}
    tokens. Emit-time templates (paths containing assets/collab-repo/ or
    legacy/) are skipped during directory discovery — they legitimately carry
    placeholders; fixture paths (tests/examples/) are exempt from the
    placeholder check only. Exit 0 = no errors (warnings allowed); exit 1 = errors.
    """
    if not path.exists():
        typer.echo(f"error: {path} does not exist", err=True)
        raise typer.Exit(2)
    findings, files, skipped = validate_mod.validate_path(path)
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    if json_out:
        _echo_json(
            {
                "files_checked": [f.as_posix() for f in files],
                "templates_skipped": [f.as_posix() for f in skipped],
                "findings": [f.to_dict() for f in findings],
                "summary": {"errors": len(errors), "warnings": len(warnings)},
            }
        )
    else:
        for f in findings:
            typer.echo(f"{f.severity.upper():7s} {f.file}: [{f.check}] {f.message}")
        if skipped:
            typer.echo(f"skipped {len(skipped)} template file(s) (assets/collab-repo, legacy)")
        typer.echo(
            f"{len(files)} file(s) checked: {len(errors)} error(s), {len(warnings)} warning(s)"
        )
    raise typer.Exit(1 if errors else 0)


# --- M2: status -----------------------------------------------------------------------


@app.command()
def status(
    collab: Path = _COLLAB_OPT,
    fetch: bool = typer.Option(
        False, "--fetch", help="git fetch each working copy first (needed to see remote-side divergence)."
    ),
    sla: int = typer.Option(14, "--sla", help="Open-handoff SLA in days."),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Divergence & staleness report across the project's working copies.

    Reads manifest.yaml (repos + optional workspace.clones / workspace.worktrees_root)
    and reports: ahead/behind origin default branch, uncommitted dirt, unmerged
    local branches with age, open handoffs past SLA, ledger staleness vs
    code-repo activity (heuristic), and a stale wiki/status.md. Exit 0 = green
    (warnings allowed); exit 1 = at least one red finding (CI-usable).
    """
    try:
        findings = status_mod.collect(collab.resolve(), fetch=fetch, sla_days=sla)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(2)
    reds = [f for f in findings if f.severity == status_mod.RED]
    if json_out:
        _echo_json(
            {
                "generated": clock.today().isoformat(),
                "collab": collab.resolve().as_posix(),
                "sla_days": sla,
                "findings": [f.to_dict() for f in findings],
                "summary": {"red": len(reds), "warn": len(findings) - len(reds)},
            }
        )
    else:
        typer.echo(status_mod.render_table(findings))
    raise typer.Exit(1 if reds else 0)


# --- M3: ledgers ----------------------------------------------------------------------

finding_app = typer.Typer(help="Findings ledger (findings/index.md).", no_args_is_help=True)
decision_app = typer.Typer(help="Decisions ledger (decisions/index.md).", no_args_is_help=True)
app.add_typer(finding_app, name="finding")
app.add_typer(decision_app, name="decision")


def _ledger_new(
    kind: str,
    collab: Path,
    title: str,
    author: str,
    body_file: Optional[Path],
    no_push: bool,
    retries: int,
) -> None:
    body: str | None = None
    if body_file is not None:
        if not body_file.is_file():
            typer.echo(f"error: --body-file {body_file} not found", err=True)
            raise typer.Exit(2)
        body = body_file.read_text(encoding="utf-8")
    try:
        n = ledger.add_entry(
            collab.resolve(),
            kind,
            title=title,
            author=author,
            body=body,
            push=not no_push,
            retries=retries,
        )
    except (ledger.LedgerError,) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)
    prefix = ledger.KINDS[kind].prefix
    pushed = "committed (not pushed)" if no_push else "committed and pushed"
    typer.echo(f"{prefix}{n} — {title} ({pushed})")


@finding_app.command("new")
def finding_new(
    title: str = typer.Option(..., "--title", help="Finding title (goes in the heading)."),
    author: str = typer.Option(..., "--author", help="Persona/author name for the entry."),
    body_file: Optional[Path] = typer.Option(
        None, "--body-file", help="File whose content becomes the entry body (default: a stub)."
    ),
    collab: Path = _COLLAB_OPT,
    no_push: bool = typer.Option(False, "--no-push", help="Commit locally only (offline)."),
    retries: int = typer.Option(
        3, "--retries", help="Push-rejection retries (fetch+rebase+renumber)."
    ),
) -> None:
    """Allocate the next F-number and append a house-style entry.

    Allocation is race-safe by push-retry: on push rejection baron rolls back,
    rebases onto origin, re-parses the index, renumbers, and retries (bounded).
    """
    _ledger_new("finding", collab, title, author, body_file, no_push, retries)


@decision_app.command("new")
def decision_new(
    title: str = typer.Option(..., "--title", help="Decision title (goes in the heading)."),
    author: str = typer.Option(..., "--author", help="Persona/author name for the entry."),
    body_file: Optional[Path] = typer.Option(
        None, "--body-file", help="File whose content becomes the entry body (default: a stub)."
    ),
    collab: Path = _COLLAB_OPT,
    no_push: bool = typer.Option(False, "--no-push", help="Commit locally only (offline)."),
    retries: int = typer.Option(
        3, "--retries", help="Push-rejection retries (fetch+rebase+renumber)."
    ),
) -> None:
    """Allocate the next D-number and append a house-style entry (same race-safe
    push-retry allocation as `baron finding new`)."""
    _ledger_new("decision", collab, title, author, body_file, no_push, retries)


# --- M3: handoffs ---------------------------------------------------------------------

handoff_app = typer.Typer(
    help="_handoff/ lifecycle: create -> close -> archive (never delete).",
    no_args_is_help=True,
)
app.add_typer(handoff_app, name="handoff")


@handoff_app.command("create")
def handoff_create(
    for_: str = typer.Option(..., "--for", help="Addressee persona (or `all`)."),
    from_: str = typer.Option(..., "--from", help="Sending persona."),
    title: str = typer.Option(..., "--title", help="Handoff title (also drives the filename slug)."),
    priority: str = typer.Option("medium", "--priority", help="low | medium | high."),
    collab: Path = _COLLAB_OPT,
    no_commit: bool = typer.Option(False, "--no-commit", help="Write the file without committing."),
) -> None:
    """Write _handoff/YYYY-MM-DD-<slug>.md with standard frontmatter (status: open)."""
    if priority not in handoff_mod.PRIORITIES:
        typer.echo(f"error: --priority must be one of {handoff_mod.PRIORITIES}", err=True)
        raise typer.Exit(2)
    try:
        path = handoff_mod.create(
            collab.resolve(),
            for_=for_,
            from_=from_,
            title=title,
            priority=priority,
            commit=not no_commit,
        )
    except handoff_mod.HandoffError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)
    typer.echo(path.as_posix())


@handoff_app.command("close")
def handoff_close(
    file: Path = typer.Argument(..., help="The handoff file (path, or bare filename in _handoff/)."),
    note: Optional[str] = typer.Option(None, "--note", help="Closing note (added as a blockquote)."),
    collab: Path = _COLLAB_OPT,
    no_commit: bool = typer.Option(False, "--no-commit", help="Move without git (no history-preserving mv)."),
) -> None:
    """Flip status to done (+ closed: date, optional note) and git-mv the file
    to _handoff/archive/YYYY/ — archive, never delete."""
    try:
        dest = handoff_mod.close(
            collab.resolve(), file, note=note, commit=not no_commit
        )
    except handoff_mod.HandoffError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)
    typer.echo(dest.as_posix())


@handoff_app.command("list")
def handoff_list(
    collab: Path = _COLLAB_OPT,
    open_only: bool = typer.Option(False, "--open", help="Only handoffs with status: open."),
    archived: bool = typer.Option(False, "--archived", help="Include archived handoffs."),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """List handoffs with status, addressee, sender, and age."""
    items = handoff_mod.iter_handoffs(collab.resolve(), include_archived=archived)
    if open_only:
        items = [h for h in items if h.status == "open"]
    if json_out:
        _echo_json([h.to_dict() for h in items])
        return
    if not items:
        typer.echo("no handoffs")
        return
    for h in items:
        age = f"{h.age_days}d" if h.age_days is not None else "?"
        typer.echo(
            f"{h.status:6s} {h.path.name}  for={h.for_} from={h.from_} "
            f"priority={h.priority} age={age}"
        )


# --- M3: index ------------------------------------------------------------------------


@app.command()
def index(
    collab: Path = _COLLAB_OPT,
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Regenerate the BARON INDEX block in _handoff/README.md and verify ledger
    numbering (duplicates = error; gaps / out-of-order = report-only warnings —
    baron never renumbers history)."""
    root = collab.resolve()
    readme = indexer.update_readme(root)
    reports = [r for k in indexer.KINDS if (r := indexer.check_ledger(root, k)) is not None]
    duplicates = any(r.duplicates for r in reports)
    if json_out:
        _echo_json(
            {
                "readme": readme.as_posix(),
                "ledgers": [r.to_dict() for r in reports],
            }
        )
    else:
        typer.echo(f"wrote {readme.as_posix()}")
        for r in reports:
            if r.duplicates:
                typer.echo(f"ERROR   {r.kind}s: duplicate IDs {r.duplicates}")
            if r.gaps:
                typer.echo(f"warning {r.kind}s: numbering gaps at {r.gaps} (report-only)")
            if r.out_of_order:
                typer.echo(f"warning {r.kind}s: out-of-order headings at {r.out_of_order} (report-only)")
            if not (r.duplicates or r.gaps or r.out_of_order):
                typer.echo(f"ok      {r.kind}s: numbering duplicate-free and monotonic")
    raise typer.Exit(1 if duplicates else 0)


def main() -> None:  # pragma: no cover - console-script convenience
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
