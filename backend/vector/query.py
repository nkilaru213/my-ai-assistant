from __future__ import annotations

from .embedder import LocalEmbedder
from .chroma_store import ChromaStore

class VectorRetriever:
    def __init__(self, persist_dir: str, collection_name: str):
        self.embedder = LocalEmbedder()
        self.store = ChromaStore(persist_dir=persist_dir, collection_name=collection_name)

    def retrieve(self, query: str, k: int = 5, where: dict | None = None) -> list[dict]:
        # light query expansion helps short triage queries (e.g., "issue with VPN")
        expanded = (
            f"Endpoint issue description: {query}
"
            f"Consider: VPN/connectivity/authentication/DNS/certificates/routing/client.
"
        )
        q_emb = self.embedder.embed([expanded])[0]
        res = self.store.query_by_embedding(q_emb, n_results=k, where=where)

        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        out = []
        for i in range(len(docs)):
            out.append({
                "text": docs[i],
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dists[i] if i < len(dists) else None,
            })
        return out
