"""Throwaway demo of vector search.

    python -m app.rag.demo_vector_search
    python -m app.rag.demo_vector_search "your own question"
"""

import sys

from app.config import settings
from app.rag.retriever import retrieve
from app.rag.vector_store import count

DEFAULT_QUERIES = [
    "the whole family was together",
    "a trip with the family",
    "a birthday celebration",
    "photos from 2024",
    "playing football",
    "a wedding in Paris",
]

if __name__ == "__main__":
    print(f"Memories in index: {count()}   (provisional threshold: {settings.semantic_min_score})")
    for query in sys.argv[1:] or DEFAULT_QUERIES:
        print(f'\nQuery: "{query}"')
        hits = retrieve(query, top_k=3)
        if not hits:
            print("  (nothing)")
        for hit in hits:
            flag = "" if hit.score >= settings.semantic_min_score else "   <- below threshold"
            print(f"  {hit.score:.3f}  #{hit.photo_id}: {hit.text[:80]}{flag}")