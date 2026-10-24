"""Keep the vector index in step with the database."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models import Photo
from app.database.session import SessionLocal
from app.rag import vector_store
from app.rag.embeddings import embed_documents
from app.rag.memory_text import build_memory_text, effective_year_month


def index_photo(photo_id: int) -> bool:
    """(Re)build one photo's vector. Returns True if it is now searchable."""
    with SessionLocal() as session:
        photo = session.execute(
            select(Photo).options(selectinload(Photo.event)).where(Photo.id == photo_id)
        ).scalar_one_or_none()
        if photo is None:
            vector_store.remove_memory(photo_id)
            return False
        text = build_memory_text(photo)
        year, month = effective_year_month(photo)
        event_id, uploader_id = photo.event_id, photo.uploader_id

    if not text:  # nothing meaningful to embed yet
        vector_store.remove_memory(photo_id)
        return False

    vector = embed_documents([text])[0]
    vector_store.upsert_memory(photo_id, text, vector, year, month, event_id, uploader_id)
    return True


def index_all() -> tuple[int, int]:
    """Rebuild the index for every photo. Returns (indexed, skipped)."""
    with SessionLocal() as session:
        photo_ids = list(session.execute(select(Photo.id).order_by(Photo.id)).scalars())
    indexed = sum(1 for photo_id in photo_ids if index_photo(photo_id))
    return indexed, len(photo_ids) - indexed