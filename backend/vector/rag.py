from __future__ import annotations

import subprocess
from typing import Any

def build_prompt(user_query: str, contexts: list[dict[str, Any]]) -> str:
    ctx = []
    for i, c in enumerate(contexts, start=1):
        meta = c.get("metadata") or {}
        header = f"#{i} source={meta.get('source','?')} category={meta.get('category','')} file={meta.get('filename','')}".strip()
        ctx.append(f"{header}\n{c.get('text','')}\n")
    ctx_block = "\n---\n".join(ctx) if ctx else "(no context retrieved)"

    return f"""You are an Endpoint Support Triage Assistant.

User question:
{user_query}

Relevant context (top matches):
{ctx_block}

Return ONLY a JSON object with keys:
- root_cause (string)
- next_actions (array of strings)
- followup_questions (array of strings)
- confidence (0 to 1)

Be concise and action-oriented.
"""

def run_claude_cli(prompt: str, claude_bin: str = "claude") -> str:
    proc = subprocess.run(
        [claude_bin],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    out = proc.stdout.decode("utf-8", errors="ignore").strip()
    err = proc.stderr.decode("utf-8", errors="ignore").strip()
    return out if out else (err if err else "")

def synthesize(user_query: str, contexts: list[dict], claude_bin: str = "claude") -> str:
    return run_claude_cli(build_prompt(user_query, contexts), claude_bin=claude_bin)
