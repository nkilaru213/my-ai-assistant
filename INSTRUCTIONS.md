# AI Assistant — Hybrid Backend (SQLite/Postgres/Vector)

This repo now supports **switching** between:
- **sqlite** (legacy fuzzy search, current default)
- **postgres** (optional, if you have Postgres running)
- **vector** (Chroma vector DB + local embeddings + optional Claude CLI synthesis)

## 1) Setup (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Choose backend mode

Set `SEARCH_BACKEND`:

```bash
# Legacy (current behavior)
export SEARCH_BACKEND=sqlite

# Vector DB (Chroma)
export SEARCH_BACKEND=vector

# Postgres (optional)
export SEARCH_BACKEND=postgres
```

## 3) Run server

Use the existing app that has all routes:

```bash
python app_db.py
```

Default runs on `http://127.0.0.1:5000` unless you change it in code.

> If you prefer a fixed port/host, you can modify Flask app.run at the bottom, or migrate to a unified `app.py` later.

## 4) Vector mode: build index

When `SEARCH_BACKEND=vector`, you must index your KB first.

Index from SQLite KB (assistant.db):

```bash
curl -X POST http://127.0.0.1:5000/vector/index/sqlite
```

Index from uploads folders:

```bash
curl -X POST http://127.0.0.1:5000/vector/index/uploads
```

Vectors are persisted under:

- `backend/chroma_store/`

## 5) Ask questions (all modes)

Frontend posts JSON like:

```json
{ "question": "issue with vpn" }
```

You can test via curl:

```bash
curl -s -X POST http://127.0.0.1:5000/ask   -H "Content-Type: application/json"   -d '{"question":"issue with vpn"}'
```

## 6) Claude CLI (vector mode)

Vector mode can optionally synthesize answers using Claude CLI.

Enable/disable:

```bash
export CLAUDE_SYNTH=true   # default
export CLAUDE_SYNTH=false  # return top retrieved chunk instead
```

If Claude CLI is not on PATH:

```bash
export CLAUDE_BIN=/full/path/to/claude
```

## 7) Postgres mode (optional)

Set connection env vars:

```bash
export PG_HOST=localhost
export PG_PORT=5432
export PG_DB=assistant
export PG_USER=postgres
export PG_PASSWORD=...
export PG_TABLE=knowledge_base
```

Postgres mode uses a simple LIKE query as a baseline (you can upgrade to full-text later).

---

## Notes

- Your original frontend is preserved under `frontend/`.
- Your legacy backend code remains in `backend/app_db.py`, but KB lookup now uses a switchable `SearchService`.
- If you want, next we can refactor into a clean `backend/app.py` while keeping routes unchanged.
