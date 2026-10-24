"""Question in, ranked memories out."""

from app.rag.embeddings import embed_query
from app.rag.vector_store import Hit, search
from app.services.search_service import parse_query


def retrieve(query: str, top_k: int = 5, min_score: float | None = None) -> list[Hit]:
   
    filters = parse_query(query)  # reuse the Phase 7 parser for year and month
    return search(
        embed_query(query),
        top_k=top_k,
        year=filters.year,
        month=filters.month,
        min_score=min_score,
    )