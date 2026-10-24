"""Throwaway demo: shows tables and relationships working. Uses memory only."""

from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database.models import Base, Event, FamilyMember, Photo, Role

engine = create_engine("sqlite://")  # in memory, vanishes when the script ends
Base.metadata.create_all(engine)

with Session(engine) as session:
    mimi = FamilyMember(
        telegram_user_id=111, name="Mimi", family_relation="Mother", role=Role.ADMIN
    )
    trip = Event(name="Hawassa Trip 2023", date=date(2023, 12, 27), location="Hawassa")
    session.add_all([mimi, trip])
    session.flush()  # assigns ids without finishing the transaction

    session.add(
        Photo(uploader=mimi, event=trip, file_path="demo/1.jpg", description="At the lake")
    )
    session.commit()

    members = session.execute(select(FamilyMember)).scalars().all()
    print("Members:", [m.name for m in members])
    print(f"Event '{trip.name}' has {len(trip.photos)} photo(s)")
    photo = trip.photos[0]
    print(
        f"First photo uploaded by {photo.uploader.name} "
        f"({photo.uploader.family_relation}), event: {photo.event.name}"
    )