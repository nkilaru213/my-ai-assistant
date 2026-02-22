from __future__ import annotations

def chunk_text(text: str, max_chars: int = 1400, overlap: int = 200) -> list[str]:
    """Simple char-based chunking with overlap (good enough for KB + logs)."""
    text = (text or "").strip()
    if not text:
        return []
    chunks: list[str] = []
    step = max(1, max_chars - overlap)
    i = 0
    while i < len(text):
        chunk = text[i:i+max_chars].strip()
        if chunk:
            chunks.append(chunk)
        i += step
    return chunks
