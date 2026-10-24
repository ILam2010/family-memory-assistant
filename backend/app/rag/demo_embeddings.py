"""Throwaway demo: see embeddings and similarity working. Run from backend/:

    python -m app.rag.demo_embeddings
    python -m app.rag.demo_embeddings "a girl who wants to become a doctor"
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models import Photo
from app.database.session import SessionLocal
from app.rag.embeddings import cosine_similarity, embed_documents, embed_query
from app.rag.memory_text import build_memory_text

DEFAULT_QUERIES = [
    "the whole family was together",
    "a trip with the family",
    "someone who wants to become a doctor",
    "a birthday celebration",
]


def part1_sentences() -> None:
    print("=== Part 1: meaning vs words ===")
    a = "Everyone gathered around the table for dinner."
    b = "The whole family was together."
    c = "A football match at the stadium."
    va, vb, vc = embed_documents([a, b, c])
    print(f"vector length: {len(va)}")
    print(f"A vs B (similar meaning, almost no shared words): {cosine_similarity(va, vb):.3f}")
    print(f"A vs C (different meaning):                       {cosine_similarity(va, vc):.3f}")


def part2_photos(queries: list[str]) -> None:
    print("\n=== Part 2: ranking YOUR photos by meaning ===")
    with SessionLocal() as session:
        photos = session.execute(
            select(Photo).options(selectinload(Photo.event))
        ).scalars().all()
        items = [(p.id, build_memory_text(p)) for p in photos]
    items = [(photo_id, text) for photo_id, text in items if text]
    if not items:
        print("No photos with any text yet. Upload some photos with descriptions first.")
        return

    vectors = embed_documents([text for _, text in items])
    for query in queries:
        query_vector = embed_query(query)
        scored = sorted(
            (
                (cosine_similarity(query_vector, vector), photo_id, text)
                for vector, (photo_id, text) in zip(vectors, items)
            ),
            reverse=True,
        )
        print(f'\nQuery: "{query}"')
        for score, photo_id, text in scored[:3]:
            print(f"  {score:.3f}  #{photo_id}: {text[:90]}")


if __name__ == "__main__":
    part1_sentences()
    part2_photos(sys.argv[1:] or DEFAULT_QUERIES)