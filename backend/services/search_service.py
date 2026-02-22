from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from config import (
    SEARCH_BACKEND,
    SQLITE_DB_PATH,
    CHROMA_DIR,
    COLLECTION_NAME,
    TOP_K,
    CLAUDE_BIN,
    CLAUDE_SYNTH,
    PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD, PG_TABLE,
)

# Legacy
from db_manager import DBManager

# Vector
from vector.query import VectorRetriever
from vector.rag import synthesize
from vector.ingest_sqlite import ingest_sqlite_kb
from vector.ingest_files import ingest_dir

# Postgres
from services.postgres_manager import PostgresKB


@dataclass
class SearchResult:
    answer: Optional[str]
    source: str
    confidence: float
    contexts: Optional[list[dict[str, Any]]] = None
    extra: Optional[dict[str, Any]] = None


class SearchService:
    def __init__(self):
        self.mode = SEARCH_BACKEND

        # Legacy sqlite
        self.sqlite_mgr = DBManager(str(SQLITE_DB_PATH))

        # Vector
        self.vector_retriever = VectorRetriever(str(CHROMA_DIR), COLLECTION_NAME)

        # Postgres (init lazily to avoid requiring Postgres running in other modes)
        self._pg = None

    def _pg_client(self) -> PostgresKB:
        if self._pg is None:
            self._pg = PostgresKB(
                host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD, table=PG_TABLE
            )
        return self._pg

    def index_vector_from_sqlite(self) -> dict:
        return ingest_sqlite_kb(str(SQLITE_DB_PATH), str(CHROMA_DIR), COLLECTION_NAME)

    def index_vector_from_dir(self, dir_path: str) -> dict:
        return ingest_dir(dir_path, str(CHROMA_DIR), COLLECTION_NAME)

    def search_kb(self, query: str, where: dict | None = None, top_k: int = TOP_K) -> SearchResult:
        q = (query or "").strip().lower()
        if not q:
            return SearchResult(answer=None, source=self.mode, confidence=0.0)

        if self.mode == "vector":
            contexts = self.vector_retriever.retrieve(q, k=top_k, where=where)
            if not contexts:
                return SearchResult(answer=None, source="vector", confidence=0.0, contexts=[])

            if CLAUDE_SYNTH:
                ans = synthesize(query, contexts, claude_bin=CLAUDE_BIN)
                # We keep confidence rough since CLI doesn't return scores reliably.
                return SearchResult(answer=ans, source="vector+claude", confidence=0.75, contexts=contexts)

            # No Claude synthesis: return top chunk
            top = contexts[0]
            return SearchResult(answer=top.get("text"), source="vector", confidence=0.6, contexts=contexts)

        if self.mode == "postgres":
            hits = self._pg_client().search_like(q, limit=top_k)
            if not hits:
                return SearchResult(answer=None, source="postgres", confidence=0.0)
            # Take the first hit as best
            best = hits[0]
            return SearchResult(
                answer=best.get("answer"),
                source="postgres",
                confidence=0.5,
                contexts=[{"text": f"Category: {best.get('category')}\nQ: {best.get('question')}\nA: {best.get('answer')}",
                           "metadata": {"source": "postgres", "kb_id": best.get("id"), "category": best.get("category")}}]
            )

        # default: sqlite legacy fuzzy
        row, score = self.sqlite_mgr.fuzzy_search_kb(q)
        if row:
            return SearchResult(
                answer=row["answer"],
                source="sqlite",
                confidence=float(score),
                contexts=[{"text": f"Category: {row['category']}\nQ: {row['question']}\nA: {row['answer']}",
                           "metadata": {"source": "sqlite", "kb_id": row.get("id"), "category": row["category"]}}]
            )
        return SearchResult(answer=None, source="sqlite", confidence=float(score or 0.0))
