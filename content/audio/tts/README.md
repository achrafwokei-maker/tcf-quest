# Pre-recorded content audio

MP3 files generated on the Mac by `scripts/prerender_audio.py` from this repository's original texts.
The file name is the cache key `/api/tts` uses (voice + speed + sentences), so the online beta plays them
without the voice worker or any cloud quota. Re-run the script after editing content; a test fails if a
line is missing.

Voices and attribution:
- Estelle: Pocket TTS by Kyutai (model CC-BY 4.0).
- Siwis: Piper voice fr_FR-siwis-medium (CC-BY 4.0, SIWIS French speech corpus).
- Tom: Piper voice fr_FR-tom-medium (AGPL-3.0 voice model; audio generated from it).
