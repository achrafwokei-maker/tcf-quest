# TCF Quest

Instructions for Claude working in this folder. Read this file fully at the start of every session, then read `docs/PROGRESS.md` to see where work stopped.

## Who you are working with

The owner of this project is preparing for the TCF Canada French exam (Canadian immigration, Express Entry) and building TCF Quest for their own preparation first. They are a beginner developer.

- Do the technical work yourself (install, configure, build, test, debug). Don't hand them tutorials for things you can run.
- Explain choices in plain words: what it is, why, cost, whether v1 needs it. Define jargon the first time.
- Keep updates short. After each milestone: what was built, what works, what was tested, what is incomplete, what is next.
- When there is a choice, pick one and say why. Ask them only for macOS permissions, money, publishing, destructive actions, or real product decisions.
- Never claim something works unless it was tested.

## Status

**Development approved on 2026-10-16** (free local plan). **Experience blueprint approved 2026-10-16** (`docs/EXPERIENCE_BLUEPRINT.md`; Part II = his notes, wins over Part I). Every piece of content must carry a `tcf_target` tag (TCF Canada identity). Milestones 0–4 done 2026-10-16, plus natural French voices (Pocket TTS + Piper worker, `docs/VOICE_SYSTEM.md`; any spoken text goes through `tts_text.to_speech`). Core milestones M1–M13 done 2026-10-17 (`docs/CORE_FUNCTIONAL_GAPS.md`, see Remaining limits). Companion: Céleste. Work in phases (see `docs/ROADMAP.md`), commit after each working milestone, and keep `docs/PROGRESS.md` current so any session can resume.

## Hard rules

- **US$0 budget.** No paid APIs, subscriptions or cloud services. The app uses only free, local, open-source tools. (The Claude Code subscription is for building, not for the app.)
- **Local only.** Servers bind to 127.0.0.1. Never expose the app, Ollama or files to the network without the learner's approval.
- **Private data stays private.** Learner data, recordings and the database live in `data/` (git-ignored). Never commit secrets or recordings.
- **Licences.** Only original content or properly licensed media and models. Never copy official TCF questions. Check every dependency/model licence before adding it; record it in `docs/DECISIONS.md`.
- Project-local installs only; don't change system-wide settings. Never use permission-bypass flags.

## Product rules (approved by the learner)

- Exam mode is strictly separate from gamified training: plain, quiet, timed exactly like the real exam.
- Unlocks are based on mastery, never points. XP rewards effort only.
- Never claim official scores. Always say "estimate" and show a range or confidence.
- Three scales are never mixed: CEFR (A1–C2), TCF score (331–699, or 0–20), NCLC. Show all three, labelled.
- The IRCC score table lives in a versioned config file, never hard-coded.
- Rules decide (scoring, answer keys, scheduling, unlocks); AI explains, converses and gives bounded feedback. AI never changes an answer key or awards a level.

## Exam facts (key ones)

- Listening: 39 MCQ, 35 min. Reading: 39 MCQ, 60 min. Writing: 3 tasks, 60 min. Speaking: 3 tasks, about 12 min.
- Target: NCLC 7 floor, NCLC 9 plan target. C1/C2 is a separate personal goal, tracked separately.
- IRCC TCF→NCLC table verified on canada.ca 2026-10-16 (docs/blueprint.md, section 0).
- **Verified against FEI and IRCC on 2026-10-16** (milestone 0): writing T1 60–120, T2 120–150, T3 120–180 words, speaking T1 2 min, T2 5 min 30 incl. 2 min prep, T3 4 min 30; retake wait 20 days; results valid 2 years. A writing paper can be rated "A1 non atteint" if any task misses its word range. Source of truth: `docs/TCF_SPECIFICATION.md` and `content/exam/*.json`.

## Stack

| Part | Choice | Plain words |
| --- | --- | --- |
| Web app | React + TypeScript + Vite + Tailwind CSS (`web/`) | The screens, opened in a browser on the Mac |
| Animation | Motion | Smooth, calm transitions |
| Backend | Python 3.12 + FastAPI (`server/`) | Local program that stores progress and talks to the AI |
| Database | SQLite with numbered SQL migrations | One local file holding all progress |
| AI | Ollama + Qwen3 8B (local) | Free local language model for tutor, characters, feedback |
| Speech to text | MLX Whisper (local, milestone 5) | Writes down what you said |
| Text to speech | Pocket TTS + Piper worker on 127.0.0.1:8788 (`scripts/setup_tts.sh`) | Speaks French |

Ports: web 5173, API 8787, TTS worker 8788, Ollama 11434, all on 127.0.0.1.

## Project layout

- `web/`: frontend (design tokens in `web/src/styles/tokens.css`)
- `server/`: backend (`server/tcfquest/`), migrations in `server/tcfquest/migrations/`
- `content/`: original learning content (JSON), with verified answer keys
- `scripts/`: dev and setup scripts
- `data/`: local database and recordings (git-ignored)
- `.tools/`: project-local Python and tools (git-ignored)
- `docs/`: PRODUCT_REQUIREMENTS, ARCHITECTURE, DESIGN_SYSTEM, LEARNING_SYSTEM, VOICE_SYSTEM, TCF_SPECIFICATION, ROADMAP, DECISIONS, PROGRESS, plus the original blueprint

## Commands

- `scripts/setup.sh`: install everything project-locally (safe to re-run)
- `scripts/dev.sh`: start API + web app, then open http://localhost:5173
- `scripts/test.sh`: run all automated tests

## Art direction

Fun game style, Paris-at-night palette; exam mode stays plain. Details: `docs/DESIGN_SYSTEM.md`. **Every generated image needs the learner's approval first** (log in `docs/IMAGE_REQUESTS.md`, ask, wait for yes). First mission: « Le Marché de Belleville ».

## Working style (token rules, 2026-10-16)

- Concise replies; don't restate requirements or past decisions.
- Read only files relevant to the task; reuse existing components; focused edits over rewrites.
- One well-defined feature at a time; split complex work into milestones.
- No unnecessary agents or repeated tool calls; no long reports or duplicate docs unless asked.
- Never skip tests, security or educational accuracy to save tokens.
- After each task: ≤5-line summary (completed, tested, issues, files changed, next step).
- Keep `docs/PROGRESS.md` current so sessions resume cheaply; blueprint details stay in `docs/`.

## Still needed from the learner

Exam date (if booked), daily study minutes, and whether he can get teacher-marked writing/speaking samples. Project licence choice before any public release.
