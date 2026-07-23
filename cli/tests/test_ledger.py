"""M3 acceptance: race-safe ledger ID allocation via push-retry.

The race test reproduces the F44/F45-class collision (two writers allocate the
same number): clone A and clone B both parse the same index; A pushes first; B's
push is rejected, and B must roll back, rebase, renumber, and succeed. The final
index must hold two distinct consecutive IDs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from baron import ledger

from conftest import clone, commit_file, init_bare, run_git

INDEX_SEED = """\
# Findings — Index

| # | Title |
|---|---|
| F1 | Frozen table row one |
| F2 | Frozen table row two |

---

### F3 — Newest full entry (2026-07-01, Tess)

Body of F3.
"""


@pytest.fixture
def collab_pair(tmp_path: Path) -> tuple[Path, Path, Path]:
    origin = init_bare(tmp_path / "origin" / "collab.git")
    seed = clone(origin, tmp_path / "seed")
    commit_file(seed, "findings/index.md", INDEX_SEED, "seed: findings index")
    commit_file(
        seed,
        "decisions/index.md",
        "# Decisions — Index\n\n### D1 — First (2026-07-01, Tess)\n\nBody.\n",
        "seed: decisions index",
    )
    run_git(seed, "push", "-q", "origin", "main")
    a = clone(origin, tmp_path / "clone-a")
    b = clone(origin, tmp_path / "clone-b")
    return origin, a, b


def test_scan_ids_reads_both_heading_and_table_forms() -> None:
    ids = ledger.scan_ids(INDEX_SEED, "F")
    assert ids == [1, 2, 3]
    assert ledger.next_id(INDEX_SEED, "F") == 4


def test_simple_allocation_and_push(
    collab_pair: tuple[Path, Path, Path], fixed_clock: object
) -> None:
    _, a, _ = collab_pair
    n = ledger.add_entry(a, "finding", title="Solo entry", author="Tess")
    assert n == 4
    text = (a / "findings/index.md").read_text(encoding="utf-8")
    assert "### F4 — Solo entry (2026-07-22, Tess)" in text


def test_no_push_stays_local(
    collab_pair: tuple[Path, Path, Path], fixed_clock: object
) -> None:
    _, a, _ = collab_pair
    n = ledger.add_entry(a, "decision", title="Offline call", author="Rex", push=False)
    assert n == 2
    # Nothing left origin-ward: local main is 1 ahead.
    out = run_git(a, "rev-list", "--count", "origin/main..HEAD")
    assert out.strip() == "1"


def test_race_push_rejection_renumbers_and_succeeds(
    collab_pair: tuple[Path, Path, Path], fixed_clock: object, tmp_path: Path
) -> None:
    origin, a, b = collab_pair

    # Both clones see max=F3. A allocates F4 and pushes first.
    n_a = ledger.add_entry(a, "finding", title="A's claim", author="Alfa")
    assert n_a == 4

    # B (stale — never fetched) also computes F4; its push must be rejected,
    # then it renumbers to F5 and succeeds.
    n_b = ledger.add_entry(b, "finding", title="B's claim", author="Bravo")
    assert n_b == 5

    # Origin's final index: two distinct consecutive IDs, no collision.
    check = clone(origin, tmp_path / "check")
    text = (check / "findings/index.md").read_text(encoding="utf-8")
    ids = ledger.scan_ids(text, "F")
    assert ids == [1, 2, 3, 4, 5]
    assert "### F4 — A's claim (2026-07-22, Alfa)" in text
    assert "### F5 — B's claim (2026-07-22, Bravo)" in text


def test_retry_budget_exhaustion_raises(
    collab_pair: tuple[Path, Path, Path], fixed_clock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, a, _ = collab_pair
    real_git = ledger.git

    def rejecting_git(repo, *args, check=True):  # type: ignore[no-untyped-def]
        if args and args[0] == "push":
            proc = real_git(repo, "push", "--dry-run", "origin", "HEAD", check=False)
            proc.returncode = 1  # simulate a permanently rejected push
            return proc
        return real_git(repo, *args, check=check)

    monkeypatch.setattr(ledger, "git", rejecting_git)
    with pytest.raises(ledger.LedgerError, match="retries"):
        ledger.add_entry(a, "finding", title="Doomed", author="Tess", retries=2)
