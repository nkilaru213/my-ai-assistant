
import os
import sqlite3
from difflib import SequenceMatcher

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_schema(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                question TEXT,
                answer TEXT,
                keywords TEXT
            );

            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_text TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS device_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_usage INTEGER,
                ram_usage INTEGER,
                status TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS automation_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                steps TEXT
            );

            CREATE TABLE IF NOT EXISTS endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT,
                os_version TEXT,
                last_seen TEXT,
                compliance_status TEXT
            );
            """
        )
        conn.commit()
        conn.close()

    def insert_kb(self, category: str, question: str, answer: str, keywords: str):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO knowledge_base (category, question, answer, keywords) VALUES (?, ?, ?, ?)",
            (category, question, answer, keywords),
        )
        conn.commit()
        conn.close()

    def fuzzy_search_kb(self, query: str):
        query = (query or "").lower()
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM knowledge_base")
        rows = cur.fetchall()
        conn.close()

        best = None
        best_score = 0.0

        def sim(a, b):
            return SequenceMatcher(None, a, b).ratio()

        for row in rows:
            keys = (row["keywords"] or "").split(",")
            for kw in keys:
                s = sim(query, kw.strip().lower())
                if s > best_score:
                    best_score = s
                    best = row

            s = sim(query, (row["question"] or "").lower())
            if s > best_score:
                best_score = s
                best = row

        return best, best_score

    def insert_log(self, text: str, timestamp: str):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs (log_text, timestamp) VALUES (?, ?)",
            (text, timestamp),
        )
        conn.commit()
        conn.close()

    def latest_health(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM device_health ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return row

    def insert_health(self, cpu: int, ram: int, status: str, timestamp: str):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO device_health (cpu_usage, ram_usage, status, timestamp) VALUES (?, ?, ?, ?)",
            (cpu, ram, status, timestamp),
        )
        conn.commit()
        conn.close()

    def recent_logs(self, limit: int = 5):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return rows
