from __future__ import annotations

import os
import sqlite3
import uuid
from tqdm import tqdm

from .chunking import chunk_text
from .embedder import LocalEmbedder
from .chroma_store import ChromaStore

def ingest_sqlite_kb(sqlite_db_path: str, chroma_dir: str, collection_name: str, batch_size: int = 64) -> dict:
    if not os.path.exists(sqlite_db_path):
        raise FileNotFoundError(f"SQLite DB not found: {sqlite_db_path}")

    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM knowledge_base").fetchall()
    finally:
        conn.close()

    embedder = LocalEmbedder()
    store = ChromaStore(persist_dir=chroma_dir, collection_name=collection_name)

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []

    for r in rows:
        base = (
            f"Category: {r['category']}\n"
            f"Question: {r['question']}\n"
            f"Answer: {r['answer']}\n"
            f"Keywords: {r['keywords']}\n"
        )
        for idx, ch in enumerate(chunk_text(base)):
            ids.append(f"kb_{r['id']}_{idx}_{uuid.uuid4().hex[:8]}")
            docs.append(ch)
            metas.append({"source": "sqlite_kb", "category": r["category"], "kb_id": r["id"]})

    total = 0
    for i in tqdm(range(0, len(docs), batch_size), desc="Embedding+Upserting"):
        batch_docs = docs[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        batch_metas = metas[i:i+batch_size]
        batch_emb = embedder.embed(batch_docs)
        store.upsert(batch_ids, batch_docs, batch_emb, batch_metas)
        total += len(batch_docs)

    return {"kb_rows": len(rows), "indexed_chunks": total, "collection": collection_name, "chroma_dir": chroma_dir}
