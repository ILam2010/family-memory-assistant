"""Rebuild the whole vector index from the database.

Run from backend/:  python -m app.rag.reindex
"""

from app.rag import indexing, vector_store

if __name__ == "__main__":
    indexed, skipped = indexing.index_all()
    print(f"Indexed {indexed} photo(s); {skipped} skipped (no text yet).")
    print(f"Memories now in the vector index: {vector_store.count()}")