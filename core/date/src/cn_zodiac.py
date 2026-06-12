"""Chinese zodiac animal from a lunar year."""

ANIMALS = ("鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬")


def cn_zodiac(lunar_year: int) -> str:
    return ANIMALS[(lunar_year - 4) % 12]
