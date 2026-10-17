"""Accent proxy for the TTS test clips (run after scripts/tts_eval.py, with the .tools/tts-eval Python).

Whisper is asked, with no language hint, which language each clip is. A voice that sounds
clearly French gets p(fr) close to 1; an English accent tends to lower it and raise p(en).
This is only a hint: the real judge is a human listening test.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mlx.core as mx  # noqa: E402
from huggingface_hub import snapshot_download  # noqa: E402
from mlx_whisper.audio import N_SAMPLES, log_mel_spectrogram, pad_or_trim  # noqa: E402
from mlx_whisper.decoding import detect_language  # noqa: E402
from mlx_whisper.load_models import load_model  # noqa: E402
from mlx_whisper.tokenizer import get_tokenizer  # noqa: E402
from tts_eval import OUT, load_16k  # noqa: E402


def main():
    model = load_model(snapshot_download("mlx-community/whisper-large-v3-turbo"))
    tok = get_tokenizer(model.is_multilingual, num_languages=model.num_languages)
    out = {}
    for d in sorted(p for p in OUT.iterdir() if p.is_dir()):
        ps = []
        for w in sorted(d.glob("*.wav")):
            mel = log_mel_spectrogram(pad_or_trim(mx.array(load_16k(w)), N_SAMPLES), n_mels=model.dims.n_mels)
            _, probs = detect_language(model, mel[None], tok)
            p = probs[0] if isinstance(probs, list) else probs
            ps.append((float(p.get("fr", 0)), float(p.get("en", 0))))
        fr = sum(a for a, _ in ps) / len(ps)
        en = sum(b for _, b in ps) / len(ps)
        out[d.name] = {"p_fr": round(fr, 4), "p_en": round(en, 4), "min_fr": round(min(a for a, _ in ps), 3)}
        print(f"{d.name:40s} p(fr) {fr:.4f}  p(en) {en:.4f}  min p(fr) {out[d.name]['min_fr']:.3f}", flush=True)
    (OUT / "accent.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
