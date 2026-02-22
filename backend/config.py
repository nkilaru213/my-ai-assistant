import os
from pathlib import Path

# --- App ---
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5050"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

BASE_DIR = Path(__file__).resolve().parent

# --- Uploads / persistence ---
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_store")))
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# --- Legacy SQLite DB (current repo uses assistant.db) ---
SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "assistant.db")))

# --- Mode switch ---
# sqlite   -> legacy fuzzy search from SQLite (DBManager.fuzzy_search_kb)
# postgres -> use Postgres KB table (same schema as SQLite knowledge_base)
# vector   -> use Chroma vector DB (local) + optional Claude CLI synthesis
SEARCH_BACKEND = os.getenv("SEARCH_BACKEND", "sqlite").lower()

# --- Vector settings ---
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION", "endpoint_kb")
TOP_K = int(os.getenv("TOP_K", "5"))

# --- Claude CLI (used only when SEARCH_BACKEND=vector and CLAUDE_SYNTH=true) ---
CLAUDE_BIN = os.getenv("CLAUDE_BIN", "claude")
CLAUDE_SYNTH = os.getenv("CLAUDE_SYNTH", "true").lower() == "true"

# --- Postgres settings (only when SEARCH_BACKEND=postgres) ---
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "assistant")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")
PG_TABLE = os.getenv("PG_TABLE", "knowledge_base")
