from __future__ import annotations

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class LocalEmbedder:
    """Local embeddings (no API keys required)."""
    def __init__(self) -> None:
        self.model = SentenceTransformer(_MODEL_NAME)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs = self.model.encode(texts, normalize_embeddings=True)
        return vecs.tolist()
