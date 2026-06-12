"""Birthday CLI — compose the atomic date utils and print the full set.

bazel run //core/date:birthday_cli -- 1999 --chinese 八月十一
bazel run //core/date:birthday_cli -- 1998 --gregorian 0906
"""

import argparse

from core.date.src.cn_md import cn_md
from core.date.src.cn_zodiac import cn_zodiac
from core.date.src.gr_md import gr_md
from core.date.src.lunar_year import lunar_year_cn, lunar_year_gr
from core.date.src.zodiac import zodiac


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("birth_year", type=int)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--gregorian", help="MMDD")
    g.add_argument("--chinese", help="e.g. 六月十三")
    args = p.parse_args()
    year = args.birth_year
    if args.gregorian:
        gregorian = args.gregorian
        chinese = cn_md(year, gregorian)
        lunar = lunar_year_gr(year, gregorian)
    else:
        chinese = args.chinese
        gregorian = gr_md(year, chinese)
        lunar = lunar_year_cn(year, chinese)
    for k, v in (
        ("year", str(year)),
        ("gregorian", gregorian),
        ("chinese", chinese),
        ("zodiac", zodiac(gregorian)),
        ("cn_zodiac", cn_zodiac(lunar)),
    ):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
