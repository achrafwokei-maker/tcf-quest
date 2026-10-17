"""Bridge to the local Ollama server. Only ever talks to 127.0.0.1."""

from __future__ import annotations

import os

import httpx

OLLAMA_URL = os.environ.get("TCFQUEST_OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("TCFQUEST_MODEL", "qwen3:8b")


async def status() -> dict:
    """Is Ollama running, and is our model installed?"""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            version = (await client.get(f"{OLLAMA_URL}/api/version")).json().get("version")
            tags = (await client.get(f"{OLLAMA_URL}/api/tags")).json().get("models", [])
    except (httpx.HTTPError, ValueError):
        return {"running": False, "model": MODEL, "model_installed": False, "version": None}
    names = {m.get("name") for m in tags}
    return {
        "running": True,
        "version": version,
        "model": MODEL,
        "model_installed": MODEL in names,
    }
