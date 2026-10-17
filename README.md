# TCF Quest

A personal, story-driven trainer for the **TCF Canada** French exam. It measures the four skills separately, decides what to study each day, and proves progress with exam-style practice, all running **locally on your Mac** with free, open-source AI.

> Practice estimates only. TCF Quest never produces official TCF results.

## Run it

Requirements: macOS on Apple Silicon, Node.js 20+, Git, and [Ollama](https://ollama.com) with the `qwen3:8b` model (`ollama pull qwen3:8b`).

```bash
git clone https://github.com/achrafwokei-maker/tcf-quest.git && cd tcf-quest
scripts/setup.sh       # first time only: installs everything inside this folder
scripts/setup_tts.sh   # optional (~3 GB): natural French voices + local speech recognition
scripts/dev.sh         # starts the app; open http://localhost:5173 in Chrome or Safari
scripts/test.sh        # runs all automated checks
```

## What's inside

- **One journey** from day one to exam readiness: briefing, an adaptive four-skill level check, six stages (A1→C2) of TCF-specific missions, weekly trials and a full 2 h 47 mock.
- **Adaptive engine**: weak points tracked by concept and confirmed fixed only on unseen questions; a daily plan built from your evidence, exam date and available time.
- **Speaking and writing** for all three TCF tasks, with a local AI examiner and rubric feedback (unofficial estimates, no pronunciation scoring).
- **Strict exam mode**: one listening, no hints, real timings; post-exam report with possible causes and next week's focus.
- Everything runs on your Mac with free models; no account, no cloud, no data leaves the computer.

Everything listens on `127.0.0.1` only; nothing is reachable from other devices.

## Your data

Progress lives in `data/tcfquest.db` (never committed). Back it up from the API (`POST /api/backup`), or copy the file while the app is stopped.

## Project map

| Folder | What's inside |
| --- | --- |
| `web/` | The screens (React + TypeScript + Tailwind) |
| `server/` | Local API, learning engine, AI bridge (Python + FastAPI + SQLite) |
| `content/` | Original lessons and questions with verified answer keys |
| `docs/` | Product, architecture, design, learning, voice and exam specs; roadmap; decisions; progress log |
| `scripts/` | Setup, run and test scripts |

## Licence and credits

- Code: [MIT](LICENSE). Learning content (`content/`): [CC BY-NC-SA 4.0](content/LICENSE.md).
- Models and engines are downloaded by the setup scripts and keep their own licences: Ollama (MIT) and Qwen3 (Apache-2.0); Pocket TTS (MIT code, CC-BY 4.0 model); Piper (GPL-3.0, run as a separate process) with voices under CC-BY / CC-BY-SA / AGPL; MLX Whisper (MIT). Details in `docs/DECISIONS.md`.
- TCF Quest is an independent study tool. It is not affiliated with France Éducation international or IRCC, its questions are original, and its results are practice estimates, never official scores.
