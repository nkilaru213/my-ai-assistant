#!/bin/bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://127.0.0.1:5000}

echo "Indexing SQLite KB -> Chroma..."
curl -s -X POST "$BASE_URL/vector/index/sqlite" | python -m json.tool

echo ""
echo "Indexing uploads -> Chroma..."
curl -s -X POST "$BASE_URL/vector/index/uploads" | python -m json.tool
