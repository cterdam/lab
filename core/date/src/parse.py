"""Parse a date string (YYYYMMDD or YYYY-MM-DD) into a datetime.date."""

import datetime
import re

_DATE_RE = re.compile(r"^\d{4}-?\d{2}-?\d{2}$")


def parse_date(val) -> datetime.date | None:
    """The date, or None if `val` (str or int) does not parse."""
    s = str(val)
    if not _DATE_RE.match(s):
        return None
    s = s.replace("-", "")
    return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
