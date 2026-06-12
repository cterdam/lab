"""Lunisolar month-day of a Gregorian date (year + MMDD)."""

from lunardate import LunarDate

from core.date.src.cn_str import format_cn_md


def cn_md(year: int, gr_md: str) -> str:
    lunar = LunarDate.fromSolarDate(year, int(gr_md[:2]), int(gr_md[2:4]))
    return format_cn_md(lunar.month, lunar.day, lunar.isLeapMonth)
