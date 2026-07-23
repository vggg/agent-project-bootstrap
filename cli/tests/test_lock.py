"""M5 acceptance: PR-as-lock via a recorded fake forge (no live ``gh``).

The FakeForge implements the Forge Protocol surface lock.py consumes and
records every call, so the tests assert both behavior (claim / double-claim
refusal / release / list) and the exact forge interactions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from baron import lock
from baron.forge import Forge


class FakeForge:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.prs: list[dict] = []
        self._next = 1

    # --- Protocol surface ---
    def available(self) -> bool:
        return True

    def default_branch(self, repo: Path) -> str | None:
        self.calls.append(("default_branch", repo))
        return "main"

    def create_branch(self, repo: Path, *, branch: str, base: str, message: str) -> None:
        self.calls.append(("create_branch", branch, base, message))

    def open_pr(
        self,
        repo: Path,
        *,
        title: str,
        body: str,
        base: str | None = None,
        draft: bool = False,
        head: str | None = None,
        labels: list[str] | None = None,
    ) -> str:
        number = self._next
        self._next += 1
        pr = {
            "number": number,
            "title": title,
            "headRefName": head or "",
            "labels": [{"name": l} for l in labels or []],
            "author": {"login": "vggg"},
            "createdAt": "2026-07-20T12:00:00Z",
            "url": f"https://example.invalid/pr/{number}",
        }
        self.prs.append(pr)
        self.calls.append(("open_pr", title, base, draft, head, tuple(labels or [])))
        return str(pr["url"])

    def list_open_prs(self, repo: Path) -> list[dict[str, object]]:
        self.calls.append(("list_open_prs",))
        return [dict(pr) for pr in self.prs]

    def close_pr(self, repo: Path, number: int, *, delete_branch: bool = False) -> None:
        self.calls.append(("close_pr", number, delete_branch))
        self.prs = [pr for pr in self.prs if pr["number"] != number]


@pytest.fixture
def forge() -> FakeForge:
    fake = FakeForge()
    assert isinstance(fake, Forge)  # the runtime-checkable Protocol holds
    return fake


REPO = Path("/synthetic/code")


def test_claim_happy_path(forge: FakeForge, fixed_clock: object) -> None:
    url = lock.claim(
        REPO, "contracts/models.py", reason="tightening the stage protocol", forge=forge
    )
    assert url == "https://example.invalid/pr/1"
    assert ("create_branch", "lock/contracts-models-py", "main",
            "lock: claim contracts/models.py") in forge.calls
    open_call = next(c for c in forge.calls if c[0] == "open_pr")
    assert open_call[1] == "lock: contracts/models.py"
    assert open_call[3] is True  # draft
    assert open_call[4] == "lock/contracts-models-py"
    assert open_call[5] == ("lock:contracts/models.py",)


def test_double_claim_refused_with_holder(forge: FakeForge, fixed_clock: object) -> None:
    lock.claim(REPO, "contracts/models.py", forge=forge)
    with pytest.raises(lock.LockError) as excinfo:
        lock.claim(REPO, "contracts/models.py", reason="me too", forge=forge)
    message = str(excinfo.value)
    assert "already locked" in message
    assert "vggg" in message  # shows the holder
    assert "#1" in message
    # No second branch/PR was created.
    assert sum(1 for c in forge.calls if c[0] == "create_branch") == 1
    assert sum(1 for c in forge.calls if c[0] == "open_pr") == 1


def test_different_paths_do_not_collide(forge: FakeForge, fixed_clock: object) -> None:
    lock.claim(REPO, "contracts/models.py", forge=forge)
    lock.claim(REPO, "contracts/stages.py", forge=forge)
    assert len(forge.prs) == 2


def test_release_closes_pr_and_deletes_branch(
    forge: FakeForge, fixed_clock: object
) -> None:
    lock.claim(REPO, "contracts/models.py", forge=forge)
    number = lock.release(REPO, "contracts/models.py", forge=forge)
    assert number == 1
    assert ("close_pr", 1, True) in forge.calls
    assert lock.list_locks(REPO, forge=forge) == []


def test_release_without_lock_refuses(forge: FakeForge) -> None:
    with pytest.raises(lock.LockError, match="nothing to release"):
        lock.release(REPO, "contracts/models.py", forge=forge)


def test_list_reports_path_holder_age_pr(forge: FakeForge, fixed_clock: object) -> None:
    lock.claim(REPO, "contracts/models.py", forge=forge)
    lock.claim(REPO, "schema/migrations", forge=forge)
    locks = lock.list_locks(REPO, forge=forge)
    assert [l.path for l in locks] == ["contracts/models.py", "schema/migrations"]
    first = locks[0]
    assert first.holder == "vggg"
    assert first.pr_number == 1
    assert first.age_days == 2  # createdAt 2026-07-20 vs fixed clock 2026-07-22
    table = lock.render_table(locks)
    assert "contracts/models.py" in table
    assert "vggg" in table
    assert "#1" in table


def test_non_lock_prs_are_ignored(forge: FakeForge, fixed_clock: object) -> None:
    forge.open_pr(
        Path("."), title="feat: something", body="", head="dev/feat", labels=["feature"]
    )
    assert lock.list_locks(REPO, forge=forge) == []
