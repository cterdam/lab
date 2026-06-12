"""Codec for lunisolar month-day strings (六月十三, 閏十二月初一)."""

_D = "一二三四五六七八九十"
_MONTHS = {
    "正": 1,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
}


def parse_cn_md(s: str) -> tuple[int, int, bool]:
    """六月十三 -> (6, 13, False); 閏十二月初一 -> (12, 1, True)."""
    leap = s.startswith("閏")
    body = s[1:] if leap else s
    month_str, _, day_str = body.partition("月")
    month = _MONTHS[month_str]
    if day_str.startswith("初"):
        day = 10 if day_str == "初十" else _D.index(day_str[1]) + 1
    elif day_str == "三十":
        day = 30
    elif day_str == "二十":
        day = 20
    elif day_str.startswith(("二十", "廿")):
        day = 20 + _D.index(day_str[-1]) + 1
    elif day_str.startswith("十"):
        day = 10 + _D.index(day_str[1]) + 1
    else:
        raise ValueError(s)
    return month, day, leap


def format_cn_md(month: int, day: int, leap: bool) -> str:
    months = [
        "正",
        "二",
        "三",
        "四",
        "五",
        "六",
        "七",
        "八",
        "九",
        "十",
        "十一",
        "十二",
    ]
    if day <= 10:
        d = "初十" if day == 10 else "初" + _D[day - 1]
    elif day < 20:
        d = "十" + _D[day - 11]
    elif day == 20:
        d = "二十"
    elif day < 30:
        d = "廿" + _D[day - 21]
    else:
        d = "三十"
    return ("閏" if leap else "") + months[month - 1] + "月" + d
