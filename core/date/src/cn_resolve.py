"""Solar date of a lunisolar birthday in a Gregorian birth year.

A late lunisolar month can fall in the next solar year, so the lunar year is
the birth year or the one before — whichever lands the date inside the birth
year.
"""

import datetime

from lunardate import LunarDate

from core.date.src.cn_str import parse_cn_md


def cn_resolve(year: int, cn_md: str) -> datetime.date:
    month, day, leap = parse_cn_md(cn_md)
    for lunar_year in (year, year - 1):
        try:
            solar = LunarDate(lunar_year, month, day, leap).toSolarDate()
        except ValueError:
            continue
        if solar.year == year:
            return solar
    raise ValueError(f"{cn_md!r} has no date in {year}")
