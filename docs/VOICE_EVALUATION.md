# French voice evaluation (2026-10-16)

The goal is to replace the robotic voice with natural French voices that are free and local. Target: ≥ 4/5 in the learner's listening test.

## Why the old voice sounded robotic and said "slash"

- `speak.ts` picked the first local `fr-FR` browser voice. On this Mac that is **Eddy**, a
  low-quality novelty voice. No Premium/Enhanced French voices are installed.
- The raw display text was sent to the voice. So "Pourquoi… ? / Quand… ?" was read with "slash"
  and stray pauses, and Markdown, `M.`, `€` and numbers were read literally.

## Method

- **Corpus:** 12 sentences covering what learners hear:
  - punctuation, a slash list and questions
  - accents and liaison ("Les enfants ont attendu")
  - abbreviations (`M.`, `1er`), a price, units (`11 h`, `10 kg`)
  - formal B2 syntax and dialogue
- **Pipeline:** every sentence goes through the normaliser, then each voice synthesises it.
- **Clarity:** local Whisper large-v3-turbo transcribes each clip, and I compute the character error
  rate (CER) against the spoken text. Numbers written as digits vs words count as equal.
- **Accent hint:** Whisper's language detection on each clip, with no hint given.
- **Measurements:** speed on this Mac (CPU) and any symbol words read aloud.
- **Tools:** `scripts/tts_eval.py` and `scripts/tts_accent.py`. The raw results and every WAV are in
  `models/tts-eval/` (not in git).

**What the numbers can't tell:** naturalness, rhythm and intonation. Claude can't hear audio, so
the final judgement is the learner's 1–5 rating in the Voice Studio.

## Results (16 voices, 12 sentences each)

| Voice | Engine | Speaker | CER ↓ | p(French) avg / worst clip | Time per sentence | Licence |
| --- | --- | --- | --- | --- | --- | --- |
| Estelle ♀ | Pocket TTS | French | 0.039 | 0.991 / 0.90 | ~0.7 s | CC-BY 4.0 model, Kyutai voice |
| Siwis ♀ | Piper | French | 0.010 | 0.999 / 1.00 | 0.23 s | CC-BY 4.0 |
| Jessica ♀ | Piper (UPMC) | French | 0.033 | 0.992 / 0.92 | ~0.1 s | CC-BY-SA 4.0 |
| George ♂ | Pocket TTS | English (VCTK) | **0.001** | 0.994 / 0.96 | ~0.9 s | CC-BY 4.0 |
| Paul ♂ | Pocket TTS | English (VCTK) | 0.005 | 0.998 / 1.00 | ~0.9 s | CC-BY 4.0 |
| Jean ♂ | Pocket TTS | English (EARS) | 0.010 | 0.980 / **0.79** | ~0.9 s | CC-BY-NC 4.0, personal use only |
| Charles ♂ | Pocket TTS | English (VCTK) | 0.022 | 0.998 / 1.00 | ~0.9 s | CC-BY 4.0 |
| Marius ♂ | Pocket TTS | voice donation | 0.050 | 0.998 / 0.99 | ~0.9 s | Kyutai voice donation |
| Tom ♂ | Piper | French | 0.011 | 0.999 / 1.00 | ~0.1 s | AGPL-3.0 voice |
| Pierre ♂ | Piper (UPMC) | French | 0.023 | 0.994 / 0.94 | 0.10 s | CC-BY-SA 4.0 |
| Gilles ♂ (16 kHz) | Piper | French | 0.031 | 0.999 / 0.99 | ~0.1 s | CC0 |
| Thomas ♂ | macOS | French | 0.005 | 0.999 / 1.00 | 1.3 s | Apple, local only |
| Amélie ♀ (fr-CA) | macOS | French | 0.024 | 0.998 / 0.99 | ~1 s | Apple |
| Jacques ♂ | macOS | French | 0.040 | 0.995 / 0.98 | ~1 s | Apple |
| Eddy ♂ *(old app voice)* | macOS | — | 0.047 | 0.996 / 0.98 | ~1 s | Apple |
| Flo ♀ | macOS | — | 0.143 | 0.980 / 0.91 | ~1 s | Apple |

**Symbol words read aloud:** 0 for every voice once the text is normalised. Before normalising,
every engine would read the slash in sentence 6.

## Findings

- **Pocket TTS works well in French.**
  - Its native voice Estelle is understood almost perfectly. Its higher CER comes from a single
    sentence: the old "Pourquoi ? / Quand ?" list.
  - The English-speaker voices transfer to French with very low error. The accent hint is small but
    real: **Jean** sounds the least French (one clip only 79 % "French"), which matches Kyutai's warning.
  - For French learners, avoid voices with any accent risk: Jean is listed but marked "English
    speaker", and the default male voice is a native French one.
- **Piper is fastest** (≈0.1–0.2 s per sentence) and can slow down for real.
  - It logs a missing nasal-tilde phoneme ("Missing phoneme from id map: ̃") for every voice, so some
    nasal vowels (an/on/in) may be flattened.
  - Listen for it in "Un bon vin blanc".
- **Every finalist beats Eddy** (the old voice) on clarity, except Marius.
- **Speed:** Pocket generates at about 4× real time on the CPU. A line is ready in about 1 s, and
  replays come instantly from the cache.

## Defaults (until the learner's ratings say otherwise)

| Slot | Default | Why |
| --- | --- | --- |
| Female (Madame Roux, Céleste) | **Pocket · Estelle** | Native French, the most expressive engine, the voice Kyutai recommends for French |
| Male (M. Delaunay) | **Piper · Tom** | Native French (no accent risk), clear, natural slow speed |
| Narrator | **Piper · Siwis** | Native French, clearest female voice, different from Madame Roux |

## Acceptance

Not decided yet. It needs the learner's 1–5 ratings in the Voice Studio (`/reglages`). A voice that
scores below 4 is not kept as a default. If no male voice reaches 4, the next options are:

- Pocket's `french_24l` model (larger, slower)
- free macOS Premium French voices (a download only the learner can do in System Settings)
