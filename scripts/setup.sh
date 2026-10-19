#!/usr/bin/env bash
# Install everything TCF Quest needs, inside this folder only. Safe to re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export UV_PYTHON_INSTALL_DIR="$ROOT/.tools/python" UV_CACHE_DIR="$ROOT/.tools/uv-cache"

if [ ! -x .tools/bin/uv ]; then
  echo "→ Installing uv (Python manager) into .tools/"
  python3 -m venv .tools/bootstrap
  .tools/bootstrap/bin/pip install -q --disable-pip-version-check uv
  mkdir -p .tools/bin && ln -sf "$ROOT/.tools/bootstrap/bin/uv" .tools/bin/uv
fi

echo "→ Python 3.12 and backend packages"
.tools/bin/uv python install 3.12 >/dev/null
(cd server && "$ROOT/.tools/bin/uv" sync -q --python 3.12 --extra beta)

echo "→ Web app packages"
(cd web && npm install --no-fund --no-audit --loglevel=error)

echo "✓ Setup complete. Start the app with: scripts/dev.sh"
