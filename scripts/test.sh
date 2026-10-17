#!/usr/bin/env bash
# Run every automated check: backend tests, frontend type-check and tests.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "→ Backend tests";  (cd "$ROOT/server" && .venv/bin/python -m pytest -q -W ignore::DeprecationWarning)
echo "→ Type-check";     (cd "$ROOT/web" && npx tsc --noEmit)
echo "→ Frontend tests"; (cd "$ROOT/web" && npx vitest run)
echo "✓ All checks passed"
