#!/usr/bin/env bash
# Start the local API (127.0.0.1:8787) and the web app (http://localhost:5173).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -x "$ROOT/server/.venv/bin/uvicorn" ] || [ ! -d "$ROOT/web/node_modules" ]; then
  "$ROOT/scripts/setup.sh"
fi

(cd "$ROOT/server" && exec .venv/bin/uvicorn tcfquest.main:app --host 127.0.0.1 --port 8787 --reload --reload-dir tcfquest) &
API_PID=$!
TTS_PID=""
# Natural French voices (optional): Pocket TTS + Piper in their own environment, see scripts/setup_tts.sh
if [ -x "$ROOT/.tools/tts-eval/bin/python" ]; then
  (cd "$ROOT/server" && exec "$ROOT/.tools/tts-eval/bin/python" -m tcfquest.tts_worker --warm) &
  TTS_PID=$!
fi
trap 'kill $API_PID $TTS_PID 2>/dev/null || true' EXIT INT TERM

cd "$ROOT/web" && npx vite
