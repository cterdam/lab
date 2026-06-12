"""Gregorian month-day (MMDD) of a lunisolar birthday in a birth year."""

from core.date.src.cn_resolve import cn_resolve


def gr_md(year: int, cn_md: str) -> str:
    solar = cn_resolve(year, cn_md)
    return f"{solar.month:02d}{solar.day:02d}"
