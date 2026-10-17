# Voice system

Everything is local and free. No text or recording leaves the Mac.

## Text-to-speech (built, 2026-10-16)

```
display text ──► tts_text.to_speech() ──► sentences() ──► TTS worker ──► WAV (cached) ──► <audio>
 (unchanged)      spoken version            short lines     Pocket / Piper   data/tts-cache
```

- **Normaliser** `server/tcfquest/tts_text.py`: produces a separate spoken version; the text on
  screen never changes. It removes Markdown, quotes and dialogue dashes, and reads symbols in context:
  `/mois` → "par mois", `et/ou` → "et ou", `1/2` → "un demi", `25/12/2026` → a date, `? / ` → a pause,
  any other `/` → "ou". It also spells out `M.`/`Mme`/`n°`, times (`8 h 15`), prices (`2,40 €`), `%`, `kg`,
  ordinals and all numbers in French words, drops URLs, and keeps French spacing before `? ! :`. 47 tests.
- **Worker** `server/tcfquest/tts_worker.py` on 127.0.0.1:8788. It runs in its own Python environment
  (`.tools/tts-eval`, installed by `scripts/setup_tts.sh`) because the engines weigh about 3 GB. It
  synthesises one sentence at a time and joins sentences with natural pauses (0.18–0.38 s, depending
  on the punctuation). `scripts/dev.sh` starts it automatically when it is installed.
- **API** (`server/tcfquest/tts.py`):
  - `POST /api/tts` with `{text, speaker | voice, speed}` → WAV. The headers say which voice was used
    and whether the speed was applied natively.
  - `POST /api/tts/text` → the spoken version.
  - `GET /api/voices` → the catalogue, what is installed, and the saved settings.
  - `PUT /api/voices/settings` → saves voices, speeds, slow mode and ratings.
- **Characters keep their voice:** Madame Roux and Céleste use the female slot, M. Delaunay the male
  slot, and the Narratrice the narrator slot (`tts.CHARACTERS`). Listening items can name a `speaker`.
- **Speed 0.8×–1.2×:**
  - Piper slows down for real (`length_scale`), so the voice speaks more slowly instead of being stretched.
  - Pocket has no speed control, so the player uses pitch-preserving `playbackRate`.
  - The slow listening mode uses the saved slow speed everywhere.
  - The "Slower" button in listening items uses 0.8×.
- **Fallback:** if the worker is off, the app uses the browser voice. It reads the same normalised text
  and never picks the robotic macOS voices (Eddy, Flo, Grandpa…). It prefers Premium/Enhanced voices
  when installed (System Settings → Accessibility → Spoken Content → System voice → Manage voices).
- **Voice Studio** at `/reglages` (gear icon on Home): voice per slot with previews, both speeds,
  slow mode, and a 1–5 rating per voice. The ratings are the human acceptance test (target ≥ 4/5).

The evaluation is in [VOICE_EVALUATION.md](VOICE_EVALUATION.md).

## Speaking pipeline (M5 built 2026-10-17: capture + transcription; M6 adds the examiner)

1. Learner presses the mic → browser records → converted in the browser to 16 kHz mono WAV.
2. Backend: MLX Whisper transcribes the French (already installed for the TTS evaluation).
3. Qwen3 8B (Ollama) returns the character's reply as short spoken sentences, without Markdown, plus optional corrections as JSON.
4. Reply → TTS (the character's voice) → played. Transcript shown.

## Limits to be honest about

- Pronunciation feedback only where the evidence supports it.
- Local TTS is good but not a human recording.
- Pocket's English-speaker voices may carry an English accent in French.
