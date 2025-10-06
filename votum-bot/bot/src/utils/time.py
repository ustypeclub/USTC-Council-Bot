"""Time parsing utilities.

This module contains helper functions to parse human‑readable durations such as
"2h" or "30m" into seconds.  It also converts durations into `datetime`
objects relative to now.  Only simple suffixes (m for minutes, h for hours,
d for days) are supported.
"""

from __future__ import annotations

import datetime
import re
from typing import Optional


_DURATION_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[smhd])$")


def parse_duration(spec: str) -> Optional[datetime.timedelta]:
    """Parse a duration specification into a ``datetime.timedelta``.

    Supported suffixes:

    * ``s`` – seconds
    * ``m`` – minutes
    * ``h`` – hours
    * ``d`` – days

    Examples
    --------

    >>> parse_duration("2h")
    datetime.timedelta(seconds=7200)
    >>> parse_duration("30m")
    datetime.timedelta(seconds=1800)

    Parameters
    ----------
    spec : str
        Duration specification.

    Returns
    -------
    datetime.timedelta or None
        The parsed duration or ``None`` if the specification is invalid.
    """
    match = _DURATION_RE.match(spec.strip())
    if not match:
        return None
    value = int(match.group("value"))
    unit = match.group("unit")
    if unit == "s":
        return datetime.timedelta(seconds=value)
    elif unit == "m":
        return datetime.timedelta(minutes=value)
    elif unit == "h":
        return datetime.timedelta(hours=value)
    elif unit == "d":
        return datetime.timedelta(days=value)
    return None


def to_iso(dt: datetime.datetime) -> str:
    """Return an ISO 8601 formatted string with UTC timezone.

    >>> to_iso(datetime.datetime(2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc))
    '2024-01-01T00:00:00+00:00'
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc).isoformat()