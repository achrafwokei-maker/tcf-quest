"""AI bridge. Locally: Ollama on 127.0.0.1 (default). Online beta: Cloudflare Workers AI (free plan).

Rules decide, AI explains: callers only get text back; scores and keys stay in the rules engine.
Settings (environment):
  TCFQUEST_AI_PROVIDER   "ollama" (default) or "workers"
  TCFQUEST_CF_ACCOUNT, TCFQUEST_CF_TOKEN   Workers AI account id and API token (never in git)
  TCFQUEST_AI_DAILY_CAP  neurons per tester per day in beta (default 450)
"""

from __future__ import annotations

import base64
import json
import math
import os
from datetime import datetime, timezone

import httpx

OLLAMA_URL = os.environ.get("TCFQUEST_OLLAMA_URL", "http://127.0.0.1:11434")
CF_MODEL = os.environ.get("TCFQUEST_CF_MODEL", "@cf/meta/llama-3.1-8b-instruct-fp8-fast")
CF_STT_MODEL = "@cf/openai/whisper-large-v3-turbo"
CF_TTS_MODEL = "@cf/myshell-ai/melotts"

# Neurons per million tokens (input, output) and per audio minute, from
# https://developers.cloudflare.com/workers-ai/platform/pricing/ (checked 2026-10-19).
CF_TOKEN_RATES = {
    "@cf/meta/llama-3.1-8b-instruct-fp8-fast": (4119, 34868),
    "@cf/qwen/qwen3-30b-a3b-fp8": (4625, 30475),
}
CF_STT_PER_MIN = 46.63
CF_TTS_PER_MIN = 18.63


def provider() -> str:
    return os.environ.get("TCFQUEST_AI_PROVIDER", "ollama")


MODEL = os.environ.get("TCFQUEST_MODEL", "qwen3:8b") if provider() == "ollama" else CF_MODEL


class QuotaExceeded(ValueError):
    """Today's free AI allowance is used up. Callers treat it like any AI failure (try again later)."""


# ---------- status ----------

async def status() -> dict:
    """Is the AI reachable, and is our model available?"""
    if provider() == "workers":
        ok = bool(os.environ.get("TCFQUEST_CF_ACCOUNT") and os.environ.get("TCFQUEST_CF_TOKEN"))
        return {"running": ok, "version": "workers-ai", "model": CF_MODEL, "model_installed": ok, **budget()}
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


# ---------- chat ----------

def chat(payload: dict, timeout: float) -> str:
    """Send an Ollama-style chat payload; return the assistant's message content (a JSON string
    when payload["format"] is a schema). Raises httpx.HTTPError, ValueError or KeyError on failure."""
    if provider() != "workers":
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()["message"]["content"]
    _check_budget()
    opts = payload.get("options", {})
    body: dict = {"messages": payload["messages"], "max_tokens": opts.get("num_predict", 1500),
                  "temperature": opts.get("temperature", 0.3)}
    if "seed" in opts:
        body["seed"] = opts["seed"]
    if isinstance(payload.get("format"), dict):
        body["response_format"] = {"type": "json_schema", "json_schema": payload["format"]}
    result = _cf_run(CF_MODEL, body, timeout)
    usage = result.get("usage") or {}
    rate_in, rate_out = CF_TOKEN_RATES.get(CF_MODEL, (10000, 50000))
    record((usage.get("prompt_tokens", 0) * rate_in + usage.get("completion_tokens", 0) * rate_out) / 1e6)
    out = result["response"]
    return out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)


# ---------- speech ----------

def transcribe(wav: bytes, duration_s: float) -> dict:
    """Workers AI speech to text, in the worker's /transcribe shape."""
    _check_budget()
    result = _cf_run(CF_STT_MODEL, {"audio": base64.b64encode(wav).decode(), "language": "fr"}, 120)
    record(CF_STT_PER_MIN * max(duration_s, 1) / 60)
    segments = result.get("segments") or []
    probs = [math.exp(s["avg_logprob"]) for s in segments if "avg_logprob" in s]
    text = (result.get("text") or "").strip()
    return {"text": text, "confidence": round(sum(probs) / len(probs), 2) if probs else (0.8 if text else 0.0),
            "status": "ok" if text else "empty", "duration_s": round(duration_s, 2),
            "segments": [{"start": s.get("start"), "end": s.get("end"), "text": s.get("text", "")} for s in segments]}


def speak(text: str) -> bytes:
    """Workers AI French speech (MP3), for live lines that were not pre-recorded."""
    _check_budget()
    result = _cf_run(CF_TTS_MODEL, {"prompt": text, "lang": "fr"}, 60)
    record(CF_TTS_PER_MIN * max(len(text.split()) / 150, 0.05))  # ~150 spoken words per minute
    return base64.b64decode(result["audio"])


def _cf_run(model: str, body: dict, timeout: float) -> dict:
    account, token = os.environ["TCFQUEST_CF_ACCOUNT"], os.environ["TCFQUEST_CF_TOKEN"]
    r = httpx.post(f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}",
                   headers={"Authorization": f"Bearer {token}"}, json=body, timeout=timeout)
    if r.status_code == 429 or (r.status_code >= 400 and "neurons" in r.text.lower()):
        raise QuotaExceeded("Cloudflare daily AI allowance used up")
    r.raise_for_status()
    return r.json()["result"]


# ---------- daily allowance (beta only) ----------

def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def daily_cap() -> float:
    return float(os.environ.get("TCFQUEST_AI_DAILY_CAP", "450"))


def budget() -> dict:
    """Today's cloud AI use for the current learner. Locally there is no limit."""
    if provider() != "workers":
        return {"limited": False}
    from . import db
    conn = db.connect()
    try:
        row = conn.execute("SELECT neurons FROM ai_usage WHERE day = ?", (_today(),)).fetchone()
    finally:
        conn.close()
    used = round(row["neurons"] if row else 0.0, 1)
    return {"limited": True, "used": used, "cap": daily_cap(), "resting": used >= daily_cap()}


def _check_budget() -> None:
    if budget().get("resting"):
        raise QuotaExceeded("Your AI feedback for today is used up")


def record(neurons: float) -> None:
    from . import db
    conn = db.connect()
    try:
        conn.execute("""INSERT INTO ai_usage (day, neurons, calls) VALUES (?, ?, 1)
                        ON CONFLICT(day) DO UPDATE SET neurons = neurons + excluded.neurons, calls = calls + 1""",
                     (_today(), round(neurons, 2)))
    finally:
        conn.close()
