"""Turn a Photo record into the text that gets embedded.

Only stated facts go in. Missing fields are left out, never filled with guesses.
"""

from app.database.models import Photo
from app.services.dates import format_partial_date


def build_memory_text(photo: Photo) -> str:
    event = photo.event
    parts: list[str] = []

    if event is not None:
        parts.append(f'From the event "{event.name}".')
        if event.description:
            parts.append(" ".join(event.description.split()))

    # The photo's own date wins; otherwise use the event's.
    when = format_partial_date(photo.photo_year, photo.photo_month, photo.photo_day)
    if when is None and event is not None:
        when = format_partial_date(event.year, event.month, event.day)
    if when:
        parts.append(f"Taken in {when}.")

    location = photo.location or (event.location if event else None)
    if location:
        parts.append(f"Place: {location}.")

    if photo.people:
        parts.append(f"People: {photo.people}.")

    if photo.description:
        parts.append(" ".join(photo.description.split()))

    return " ".join(parts)


def effective_year_month(photo: Photo) -> tuple[int | None, int | None]:
    # The photo's own date if it has one, otherwise its event's date.
    if photo.photo_year is not None:
        return photo.photo_year, photo.photo_month
    if photo.event is not None:
        return photo.event.year, photo.event.month
    return None, None