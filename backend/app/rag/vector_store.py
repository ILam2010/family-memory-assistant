"""The vector database (ChromaDB): one vector per photo memory.

SQLite is the source of truth. This index can always be rebuilt from it
(see indexing.index_all), so deleting data/chroma/ never loses real data.
"""

from dataclasses import dataclass
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

COLLECTION_NAME = "family_memories"


@dataclass
class Hit:
    photo_id: int
    score: float  # cosine similarity: higher = more similar
    text: str


@lru_cache(maxsize=1)
def _collection():
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(settings.chroma_dir),
        # Private family data: don't send usage statistics anywhere.
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        configuration={"hnsw": {"space": "cosine"}},
        embedding_function=None,  # we compute embeddings ourselves
    )


def _id(photo_id: int) -> str:
    return f"photo-{photo_id}"


def upsert_memory(
    photo_id: int,
    text: str,
    vector: list[float],
    year: int | None = None,
    month: int | None = None,
    event_id: int | None = None,
    uploader_id: int | None = None,
) -> None:
    """Insert or replace one photo's vector."""
    metadata: dict[str, int] = {"photo_id": photo_id}
    # Chroma metadata can't hold None, so missing facts are simply left out.
    for key, value in (
        ("year", year), ("month", month),
        ("event_id", event_id), ("uploader_id", uploader_id),
    ):
        if value is not None:
            metadata[key] = value
    _collection().upsert(
        ids=[_id(photo_id)], embeddings=[vector], documents=[text], metadatas=[metadata]
    )


def remove_memory(photo_id: int) -> None:
    _collection().delete(ids=[_id(photo_id)])


def count() -> int:
    return _collection().count()


def search(
    query_vector: list[float],
    top_k: int = 5,
    year: int | None = None,
    month: int | None = None,
    min_score: float | None = None,
) -> list[Hit]:
    collection = _collection()
    if collection.count() == 0:
        return []

    conditions = []
    if year is not None:
        conditions.append({"year": year})
    if month is not None:
        conditions.append({"month": month})

    kwargs: dict = {
        "query_embeddings": [query_vector],
        "n_results": top_k,
        "include": ["documents", "distances"],
    }
    if len(conditions) == 1:
        kwargs["where"] = conditions[0]
    elif len(conditions) > 1:
        kwargs["where"] = {"$and": conditions}

    result = collection.query(**kwargs)

    hits: list[Hit] = []
    for item_id, document, distance in zip(
        result["ids"][0], result["documents"][0], result["distances"][0]
    ):
        score = 1.0 - distance
        if min_score is not None and score < min_score:
            continue
        hits.append(Hit(int(item_id.split("-")[1]), score, document))
    return hits