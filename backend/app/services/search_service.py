"""Structured search: turn a plain-English query into database filters."""

import re
from dataclasses import dataclass, field

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.database.models import Event, FamilyMember, Photo
from app.services.dates import MONTHS, format_partial_date

_MONTH_NAMES = {name.lower(): i for i, name in enumerate(MONTHS, start=1)}

# Filler words that carry no search meaning.
STOP_WORDS = {
    "show", "me", "find", "get", "send", "give", "see", "look", "search",
    "photos", "photo", "pictures", "picture", "pics", "pic", "images", "image",
    "from", "of", "the", "in", "a", "an", "my", "our", "all", "and", "any",
    "uploaded", "by", "with", "at", "on", "for", "to", "us", "we", "i", "please",
}


@dataclass
class SearchFilters:
    year: int | None = None
    month: int | None = None
    uploader: str | None = None
    keywords: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return (
            self.year is None
            and self.month is None
            and self.uploader is None
            and not self.keywords
        )

    def describe(self) -> str:
        parts = []
        if self.year is not None:
            parts.append(f"year {self.year}")
        if self.month is not None:
            parts.append(f"month {MONTHS[self.month - 1]}")
        if self.uploader:
            parts.append(f"uploaded by {self.uploader}")
        if self.keywords:
            parts.append("words: " + ", ".join(self.keywords))
        return "; ".join(parts)


def parse_query(text: str) -> SearchFilters:
    filters = SearchFilters()
    t = text.lower()
    t = re.sub(r"'s\b", "", t)  # "grandma's" -> "grandma"

    match = re.search(r"\b(1[89]\d\d|20\d\d)\b", t)
    if match:
        filters.year = int(match.group(1))
        t = t[: match.start()] + " " + t[match.end():]

    match = re.search(r"\b(?:uploaded )?by (\w+)", t)
    if match:
        filters.uploader = match.group(1)
        t = t[: match.start()] + " " + t[match.end():]

    for token in re.findall(r"[a-z0-9]+", t):
        if token in _MONTH_NAMES and filters.month is None:
            filters.month = _MONTH_NAMES[token]
        elif token in STOP_WORDS:
            continue
        elif token not in filters.keywords:
            filters.keywords.append(token)
    return filters


def search_photos(session: Session, filters: SearchFilters, limit: int = 10) -> list[Photo]:
    # A photo's own date wins; otherwise use its event's date.
    effective_year = func.coalesce(Photo.photo_year, Event.year)
    effective_month = case(
        (Photo.photo_year.is_not(None), Photo.photo_month), else_=Event.month
    )

    stmt = (
        select(Photo)
        .outerjoin(Event, Photo.event_id == Event.id)
        .join(FamilyMember, Photo.uploader_id == FamilyMember.id)
    )
    if filters.year is not None:
        stmt = stmt.where(effective_year == filters.year)
    if filters.month is not None:
        stmt = stmt.where(effective_month == filters.month)
    if filters.uploader:
        stmt = stmt.where(FamilyMember.name.icontains(filters.uploader, autoescape=True))

    searchable = (
        Event.name, Event.location, Event.description,
        Photo.location, Photo.description, Photo.people,
    )
    for keyword in filters.keywords:  # every keyword must match somewhere
        stmt = stmt.where(
            or_(*[column.icontains(keyword, autoescape=True) for column in searchable])
        )

    stmt = stmt.order_by(
        effective_year.desc(), effective_month.desc(), Photo.id.desc()
    ).limit(limit)
    return list(session.execute(stmt).scalars())


def format_result(photo: Photo) -> str:
    """One line per photo. Call while the database session is still open."""
    text = " ".join((photo.description or "(no description)").split())[:70]
    details = []
    if photo.event:
        details.append(photo.event.name)
    when = format_partial_date(photo.photo_year, photo.photo_month, photo.photo_day)
    if when is None and photo.event:
        when = format_partial_date(photo.event.year, photo.event.month, photo.event.day)
    if when:
        details.append(when)
    suffix = f" [{', '.join(details)}]" if details else ""
    return f"#{photo.id}: {text}{suffix}"


if __name__ == "__main__":
    samples = [
        "Show me photos from Christmas 2023",
        "photos from Hawassa",
        "pictures uploaded by Aster",
        "Find pictures with Grandma in December 2023",
        "photos from 2024",
        "Dad's birthday",
    ]
    for q in samples:
        print(f"{q!r} -> {parse_query(q)}")