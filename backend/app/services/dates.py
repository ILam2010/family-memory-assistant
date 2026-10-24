"""Partial dates: a family memory may be only a year, a month, or a full day."""

import re
from datetime import date

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_MONTH_LOOKUP = {name.lower(): i for i, name in enumerate(MONTHS, start=1)}
_MONTH_LOOKUP.update({name[:3].lower(): i for i, name in enumerate(MONTHS, start=1)})

PartialDate = tuple[int | None, int | None, int | None]  # (year, month, day)


def _validate(year: int, month: int | None, day: int | None) -> PartialDate:
    if not 1800 <= year <= 2100:
        raise ValueError("Year must be between 1800 and 2100.")
    if month is not None and not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12.")
    if day is not None:
        date(year, month, day)  # raises ValueError for impossible days like Feb 30
    return year, month, day


def parse_partial_date(text: str) -> PartialDate:
    """Accepts: 2023, 2023-12, 2023-12-27, 'December 2023', '27 December 2023'."""
    t = text.strip().lower().replace(",", "")

    m = re.fullmatch(r"(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?", t)
    if m:
        y, mo, d = m.groups()
        return _validate(int(y), int(mo) if mo else None, int(d) if d else None)

    m = re.fullmatch(r"([a-z]+) (\d{4})", t)
    if m and m.group(1) in _MONTH_LOOKUP:
        return _validate(int(m.group(2)), _MONTH_LOOKUP[m.group(1)], None)

    m = re.fullmatch(r"(\d{1,2}) ([a-z]+) (\d{4})", t)
    if m and m.group(2) in _MONTH_LOOKUP:
        return _validate(int(m.group(3)), _MONTH_LOOKUP[m.group(2)], int(m.group(1)))

    raise ValueError(
        "I couldn't read that date. Try 2023, 2023-12, 2023-12-27 or 'December 2023'."
    )


def format_partial_date(
    year: int | None, month: int | None, day: int | None
) -> str | None:
    if year is None:
        return None
    if month is None:
        return str(year)
    if day is None:
        return f"{MONTHS[month - 1]} {year}"
    return f"{day} {MONTHS[month - 1]} {year}"


if __name__ == "__main__":
    for sample in ["2023", "2023-12", "2023-12-27", "December 2023", "27 dec 2023"]:
        parsed = parse_partial_date(sample)
        print(f"{sample} -> {parsed} -> {format_partial_date(*parsed)}")
    try:
        parse_partial_date("2023-02-30")
    except ValueError:
        print("2023-02-30 -> rejected (ValueError)")