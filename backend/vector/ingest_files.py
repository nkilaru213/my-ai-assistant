from __future__ import annotations

import os
import uuid
from tqdm import tqdm

from .chunking import chunk_text
from .embedder import LocalEmbedder
from .chroma_store import ChromaStore

_TEXT_EXTS = {".txt", ".md", ".log", ".json", ".yaml", ".yml", ".csv"}

def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def ingest_dir(dir_path: str, chroma_dir: str, collection_name: str, batch_size: int = 64) -> dict:
    if not os.path.isdir(dir_path):
        return {"files_seen": 0, "indexed_chunks": 0, "skipped": 0}

    embedder = LocalEmbedder()
    store = ChromaStore(persist_dir=chroma_dir, collection_name=collection_name)

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []

    files_seen = 0
    skipped = 0

    for root, _, files in os.walk(dir_path):
        for fn in files:
            files_seen += 1
            ext = os.path.splitext(fn)[1].lower()
            if ext not in _TEXT_EXTS:
                skipped += 1
                continue
            path = os.path.join(root, fn)
            text = _read_text(path).strip()
            if not text:
                skipped += 1
                continue
            for idx, ch in enumerate(chunk_text(text)):
                ids.append(f"file_{uuid.uuid4().hex[:12]}_{idx}")
                docs.append(f"File: {fn}\nPath: {path}\n\n{ch}")
                metas.append({"source": "file", "filename": fn, "path": path})

    total = 0
    for i in tqdm(range(0, len(docs), batch_size), desc="Embedding+Upserting"):
        batch_docs = docs[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        batch_metas = metas[i:i+batch_size]
        batch_emb = embedder.embed(batch_docs)
        store.upsert(batch_ids, batch_docs, batch_emb, batch_metas)
        total += len(batch_docs)

    return {"files_seen": files_seen, "indexed_chunks": total, "skipped": skipped}
