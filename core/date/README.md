# date

Date-related utilities.

- `src/birthday.py` — Gregorian / Chinese-lunisolar birthday conversion and
  zodiac inference: given a Gregorian birth year plus either birthday, `infer`
  derives the other birthday, the Western zodiac, and the Chinese zodiac.
  Handles 閏 leap months and lunar dates that fall in the next solar year. Also a
  CLI: `bazel run //core/date:birthday_cli -- 1999 --chinese 八月十一`.

Consumed by `doc` (the ppl list's birthday-consistency check) as a Bazel module
dependency.
