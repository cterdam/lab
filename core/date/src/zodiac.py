"""Western zodiac sign from a Gregorian month-day (MMDD)."""

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


def zodiac(gr_md: str) -> str:
    month, day = int(gr_md[:2]), int(gr_md[2:4])
    for m, d, sign in _SIGNS:
        if (month, day) <= (m, d):
            return sign
    raise ValueError(gr_md)
