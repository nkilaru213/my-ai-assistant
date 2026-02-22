from __future__ import annotations

import chromadb

class ChromaStore:
    def __init__(self, persist_dir: str, collection_name: str):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.col = self.client.get_or_create_collection(name=collection_name)

    def upsert(self, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict]):
        self.col.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query_by_embedding(self, query_embedding: list[float], n_results: int = 5, where: dict | None = None):
        return self.col.query(query_embeddings=[query_embedding], n_results=n_results, where=where)
