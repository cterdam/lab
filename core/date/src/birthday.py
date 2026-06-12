"""Birthday math — Gregorian / Chinese-lunisolar conversion and zodiacs.

Given a Gregorian birth year and either a Gregorian birthday (MM-DD) or a
Chinese lunisolar one (month + day, e.g. 六月十三 / 閏十二月初一), the other
birthday, the Western zodiac, and the Chinese zodiac all follow. `infer`
returns the full set; the CLI prints them:

    bazel run //core/date:birthday -- 1999 --chinese 八月十一
    bazel run //core/date:birthday -- 1998 --gregorian 09-06
"""

import argparse
import datetime

from lunardate import LunarDate

ANIMALS = (
    "Rat",
    "Ox",
    "Tiger",
    "Rabbit",
    "Dragon",
    "Snake",
    "Horse",
    "Goat",
    "Monkey",
    "Rooster",
    "Dog",
    "Pig",
)
# (last month, last day) of each sign, in calendar order
_SIGNS = (
    (1, 19, "Capricorn"),
    (2, 18, "Aquarius"),
    (3, 20, "Pisces"),
    (4, 19, "Aries"),
    (5, 20, "Taurus"),
    (6, 20, "Gemini"),
    (7, 22, "Cancer"),
    (8, 22, "Leo"),
    (9, 22, "Virgo"),
    (10, 22, "Libra"),
    (11, 21, "Scorpio"),
    (12, 21, "Sagittarius"),
    (12, 31, "Capricorn"),
)
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


def zodiac(gregorian: str) -> str:
    month, day = int(gregorian[:2]), int(gregorian[3:5])
    for m, d, sign in _SIGNS:
        if (month, day) <= (m, d):
            return sign
    raise ValueError(gregorian)


def chinese_zodiac(lunar_year: int) -> str:
    return ANIMALS[(lunar_year - 4) % 12]


def parse_chinese(s: str) -> tuple[int, int, bool]:
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


def format_chinese(month: int, day: int, leap: bool) -> str:
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


def infer(birth_year: int, gregorian: str = None, chinese: str = None) -> dict:
    """All five fields from birth_year plus exactly one of the birthdays."""
    if gregorian:
        lunar = LunarDate.fromSolarDate(
            birth_year, int(gregorian[:2]), int(gregorian[3:5])
        )
        chinese = format_chinese(lunar.month, lunar.day, lunar.isLeapMonth)
        lunar_year = lunar.year
    elif chinese:
        month, day, leap = parse_chinese(chinese)
        for lunar_year in (birth_year, birth_year - 1):
            try:
                solar = LunarDate(lunar_year, month, day, leap).toSolarDate()
            except ValueError:
                continue
            if solar.year == birth_year:
                break
        else:
            raise ValueError(f"{chinese!r} has no date in {birth_year}")
        gregorian = f"{solar.month:02d}-{solar.day:02d}"
    else:
        raise ValueError("need one of gregorian / chinese")
    return {
        "birth_year": str(birth_year),
        "birthday_gregorian": gregorian,
        "birthday_chinese": chinese,
        "zodiac": zodiac(gregorian),
        "chinese_zodiac": chinese_zodiac(lunar_year),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("birth_year", type=int)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--gregorian", help="MM-DD")
    g.add_argument("--chinese", help="e.g. 六月十三")
    args = p.parse_args()
    for k, v in infer(args.birth_year, args.gregorian, args.chinese).items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
