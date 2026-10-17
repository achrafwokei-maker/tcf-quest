#!/usr/bin/env bash
# Natural French voices (optional, ~3 GB): Pocket TTS + Piper in their own environment, plus the
# French voice files. Everything stays inside this folder. Safe to re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export UV_PYTHON_INSTALL_DIR="$ROOT/.tools/python" UV_CACHE_DIR="$ROOT/.tools/uv-cache" HF_HOME="$ROOT/models/hf-cache"
[ -x .tools/bin/uv ] || scripts/setup.sh

echo "→ Voice engines (Pocket TTS, Piper) and the evaluation tools (MLX Whisper)"
[ -x .tools/tts-eval/bin/python ] || .tools/bin/uv venv -q --python 3.12 .tools/tts-eval
.tools/bin/uv pip install -q --python .tools/tts-eval/bin/python \
  "pocket-tts==3.3.0" "piper-tts==1.8.0" "mlx-whisper==0.4.3" soundfile scipy numpy

echo "→ French Piper voices"
mkdir -p models/piper
base="https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR"
for v in siwis/medium tom/medium upmc/medium gilles/low mls/medium; do
  name="fr_FR-${v%/*}-${v#*/}"
  for ext in onnx onnx.json; do
    [ -f "models/piper/$name.$ext" ] || curl -sfL "$base/$v/$name.$ext" -o "models/piper/$name.$ext"
  done
done

echo "→ Pocket TTS French model (first download ~400 MB)"
.tools/tts-eval/bin/python -c "from pocket_tts import TTSModel; m = TTSModel.load_model(language='french'); m.get_state_for_audio_prompt('estelle')"

echo "✓ Voices ready. scripts/dev.sh starts them automatically."
