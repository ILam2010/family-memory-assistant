"""Turn text into vectors, and compare vectors.

Memories and questions MUST be embedded with the same model,
so both live on the same "map of meaning".
"""

from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from app.config import settings

MODEL_NAME = "BAAI/bge-small-en-v1.5"  # English model, 384 numbers per text


@lru_cache(maxsize=1)
def _get_model() -> TextEmbedding:
    """Load the model once (the first call downloads it) and reuse it."""
    settings.embedding_cache_dir.mkdir(parents=True, exist_ok=True)
    return TextEmbedding(
        model_name=MODEL_NAME, cache_dir=str(settings.embedding_cache_dir)
    )


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed memory texts (done when a photo is saved)."""
    return [vector.tolist() for vector in _get_model().embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a user's question (done when someone searches)."""
    return embed_documents([text])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """1.0 = same direction (very similar meaning); near 0 = unrelated."""
    va, vb = np.asarray(a), np.asarray(b)
    return float(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)))