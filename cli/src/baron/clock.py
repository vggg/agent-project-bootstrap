"""Injectable clock — the single source of "now" for every baron command.

Every date baron writes (ledger entry dates, handoff created/closed dates, SLA
ages) comes from :func:`today` / :func:`now`. Tests inject a fixed clock via
:func:`set_clock`; production uses the system clock (UTC).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable

ClockFn = Callable[[], datetime]


def _system_now() -> datetime:
    return datetime.now(timezone.utc)


_now_fn: ClockFn = _system_now


def set_clock(fn: ClockFn) -> None:
    """Replace the clock (tests). Pass a zero-arg callable returning a datetime."""
    global _now_fn
    _now_fn = fn


def reset_clock() -> None:
    """Restore the system clock."""
    global _now_fn
    _now_fn = _system_now


def now() -> datetime:
    return _now_fn()


def today() -> date:
    return now().date()
