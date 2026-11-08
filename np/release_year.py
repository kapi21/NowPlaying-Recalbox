from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

_YEAR_MIN = 1970
_YEAR_MAX = 2035
# Values at or above this are treated as Unix seconds (Recalbox metadata API).
_UNIX_SECONDS_MIN = 10_000_000


def parse_release_year(value: Any) -> int | None:
    """Normalize Recalbox release date fields to a calendar year.

    Accepts:
    - Unix timestamp (int/str), as returned by ``/api/.../metadata/info`` ``releaseDate``
    - ISO-ish ``YYYYMMDD...`` / ``YYYY-...`` strings (gamelist style)
    - Plain year int/str in ``[_YEAR_MIN, _YEAR_MAX]``
    """
    if value is None or value == '' or value is False:
        return None
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return _from_number(int(value))

    s = str(value).strip()
    if not s:
        return None

    # Gamelist-style: 19900201T000000 or 1990-02-01
    if len(s) >= 4 and s[:4].isdigit():
        if not s.isdigit():
            y = int(s[:4])
            return y if _YEAR_MIN <= y <= _YEAR_MAX else None

    if s.isdigit():
        return _from_number(int(s))

    if len(s) >= 4 and s[:4].isdigit():
        y = int(s[:4])
        return y if _YEAR_MIN <= y <= _YEAR_MAX else None
    return None


def _from_number(n: int) -> int | None:
    if _YEAR_MIN <= n <= _YEAR_MAX:
        return n
    if n >= _UNIX_SECONDS_MIN:
        try:
            y = datetime.fromtimestamp(n, tz=timezone.utc).year
        except (OverflowError, OSError, ValueError):
            return None
        return y if _YEAR_MIN <= y <= _YEAR_MAX else None
    return None
