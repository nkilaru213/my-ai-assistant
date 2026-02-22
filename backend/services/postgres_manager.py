from __future__ import annotations

import psycopg2
from psycopg2.extras import RealDictCursor

class PostgresKB:
    """Minimal Postgres KB adapter.

    Expected table schema (same columns as SQLite knowledge_base):
      id (serial/int), category, question, answer, keywords
    """

    def __init__(self, host: str, port: int, dbname: str, user: str, password: str, table: str = "knowledge_base"):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.table = table

    def _conn(self):
        return psycopg2.connect(
            host=self.host, port=self.port, dbname=self.dbname, user=self.user, password=self.password
        )

    def search_like(self, q: str, limit: int = 5) -> list[dict]:
        # Simple LIKE search (fallback). You can improve with full-text search later.
        q_like = f"%{q}%"
        sql = f"""
        SELECT id, category, question, answer, keywords
        FROM {self.table}
        WHERE lower(question) LIKE lower(%s)
           OR lower(answer) LIKE lower(%s)
           OR lower(keywords) LIKE lower(%s)
        LIMIT %s
        """
        with self._conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (q_like, q_like, q_like, limit))
                return cur.fetchall()

    def insert(self, category: str, question: str, answer: str, keywords: str = "") -> None:
        sql = f"""INSERT INTO {self.table} (category, question, answer, keywords) VALUES (%s, %s, %s, %s)"""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (category, question, answer, keywords))
                conn.commit()
