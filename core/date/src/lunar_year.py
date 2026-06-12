"""Lunar year containing a birthday — from either birthday form.

The lunar year keys the Chinese zodiac: a date before the lunisolar new year
belongs to the previous lunar year, so it differs from the solar year exactly
when the animal would be wrong.
"""

from lunardate import LunarDate

from core.date.src.cn_resolve import cn_resolve


def lunar_year_gr(year: int, gr_md: str) -> int:
    return LunarDate.fromSolarDate(year, int(gr_md[:2]), int(gr_md[2:4])).year


def lunar_year_cn(year: int, cn_md: str) -> int:
    solar = cn_resolve(year, cn_md)
    return LunarDate.fromSolarDate(solar.year, solar.month, solar.day).year
