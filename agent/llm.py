"""
llm.py — Thin wrapper around the Ollama chat API.

Kept separate from the graph nodes so it's easy to test
and easy to swap models without touching graph logic.
"""

import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma3:12b"


def call_llm(prompt: str, model: str = DEFAULT_MODEL, system: str | None = None) -> str:
    """Send a single-turn prompt to Ollama and return the text response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
            return data["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Cannot reach Ollama at {OLLAMA_URL}. Run: ollama serve\nError: {e}"
        )