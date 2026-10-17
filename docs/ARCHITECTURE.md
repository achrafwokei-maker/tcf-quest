# Architecture

Local-first: everything runs on the Mac and is opened in a browser. Nothing listens beyond 127.0.0.1.

```
Browser (localhost:5173)
  └─ web/  React + TS + Tailwind + Motion
        │  /api/*  (Vite proxy)
        ▼
server/  FastAPI (127.0.0.1:8787)
  ├─ db.py          SQLite + numbered migrations  →  data/tcfquest.db
  ├─ ai.py          Ollama bridge                 →  127.0.0.1:11434 (qwen3:8b)
  ├─ (Phase 3) learning engine: scoring, mastery, mistakes, scheduling (deterministic)
  └─ (Phase 4) voice: Whisper STT, French TTS, audio cache in data/
content/  version-controlled JSON: chapters, missions, lessons, items + answer keys
```

## Principles

- **Rules decide, AI explains.** Answer keys, scores, unlocks and schedules are plain code over stored attempts. The AI writes explanations, plays characters and gives bounded feedback; every AI output is stored with model + prompt version (`ai_feedback`).
- **Content vs learner data.** Content is reviewed JSON in Git. The database holds only what the learner does, so estimates can be recomputed from raw `attempt` rows.
- **Thin layers, few services.** One web app, one API process, one database file, Ollama. No microservices, no cloud.
- **Future clients.** The API is plain JSON over HTTP, so a native app or hosted version can reuse it later. Local AI needs the Mac to be on; a phone can't run it alone.

## Data model (schema v1)

`profile` (single learner) · `settings` · `skill_profile` (CEFR range + confidence per skill) · `progress_history` · `attempt` · `mastery` (per competency) · `mistake` (with spaced-review fields) · `mission_progress` · `unlock` · `xp_event` · `study_day` (streak, minutes) · `achievement` · `study_plan` · `writing_submission` · `speaking_session` · `ai_feedback` · `media_asset`.

Migrations: `server/tcfquest/migrations/NNN_name.sql`, applied in order at startup; version stored in `PRAGMA user_version`.

## Backup and restore

- Backup: `POST /api/backup` writes `data/backups/tcfquest-<timestamp>.db`.
- Restore: stop the app, copy a backup over `data/tcfquest.db`, start again.

## Security

Local binding only; no secrets in code; recordings and DB git-ignored; input validated by Pydantic; Ollama reached only from the backend.

## Content format and exercise engine (milestone 1, 2026-10-16)

- **Exercise sets** live in `content/sets/<id>.json` and are validated at load by Pydantic models in `server/tcfquest/content.py`. A file whose `id` doesn't match its name, an item without a `tcf_target` tag, a task that doesn't belong to its section (e.g. `CO` + `EE-T1`), an answer key that isn't an option, duplicate options, a `type` sentence without exactly one `___`, an `arrange` alternative using different tiles, or a `listen` item without audio is rejected.
- **`tcf_target`** = `{ section: CO|CE|EO|EE, task?: EO-T1…EE-T3, purpose }`, required on every set and item, shown to the learner as « Prépare : … ».
- **Item types built:** `select`, `listen` (types 1–2), `arrange` (type 3), `type` (type 4). Speaking and writing types come later.
- **Answer keys never reach the browser** (`public_item`); the server checks answers with the deterministic rules in `server/tcfquest/checking.py` (blueprint E.2: case/punctuation/apostrophes ignored, meaning-changing accents like a/à are errors, harmless missing accents are correct with a note, one-letter slips in long words and wrong endings are partial, adjacent swaps in word order are partial).
- **Sessions** (`server/tcfquest/sessions.py`): stored in `mission_progress` as `set:<id>`; every submit writes an `attempt` (verdict, score, evidence weight, flags) before answering; wrong/partial items return once at the end; refresh resumes at the next unanswered item; stale double-submits get HTTP 409 with the current state.
- **Evidence weights** (blueprint H.1): practice 0.4, onboarding 0.1, diagnostic 1.0; ×0.5 with a hint; listening ×0.8 for 2 plays, ×0.5 for 3; listening with audio off = 0.
- **Audio (interim):** the browser's built-in French voice reads `audio.text` until local TTS files exist (`audio.file` is already supported).
- **API:** `GET /api/sets`, `GET /api/sets/{id}`, `POST /api/sets/{id}/answer`, `POST /api/sets/{id}/hint`, `POST /api/sets/{id}/restart`.

## Feedback system (milestone 2, 2026-10-16)

- **Verdict copy** for every verdict the engine can produce (keyed: correct, partial, incorrect, skipped; AI-scored later: unnatural, understood, off_task, incomplete, uncertain) lives in `web/src/lib/verdicts.ts`; a test enforces colour + icon + words and bans shaming words.
- **"Why?"** (`GET /api/sets/{id}/why/{item}`): full explanation, each option's explanation, transcript, accepted alternatives. Only available after the item was answered, so keys stay hidden. "Ask Céleste" is a placeholder until the AI milestone.
- **Learner reports** (`POST /api/attempts/{id}/flags`, table `feedback_flag`, migration 004), one per kind per attempt:
  - too_easy, too_hard, unclear → noted (for the planner and content review); evidence unchanged.
  - dispute (only on incorrect/partial) → evidence set to 0 until reviewed; original weight kept on the flag.
  - technical → evidence set to 0 permanently.
- **Review queue** (`/review`, `GET /api/review`): accept a dispute → the answer goes into `accepted_answer`, every open dispute with the same answer is accepted, those attempts become correct with their evidence restored, and the checker accepts that answer from then on. Reject → needs a reason; evidence restored, verdict unchanged. Technical → "Done" (evidence stays removed).
- **Items to fix:** ≥ 3 accepted disputes (key or prompt to rewrite) or ≥ 2 "unclear" reports (explanation to rewrite) are listed on the review page.
- Not yet: showing rejection reasons to the learner (planned with the mistake notebook, milestone 4); planner use of too_easy/too_hard (milestone 7).

## Onboarding and campaign (milestone 3, 2026-10-16)

- **Flow** (`web/src/pages/Onboarding.tsx`, `web/src/lib/onboarding.ts`): language → welcome (« Découvrir le TCF Canada » / « Je connais déjà l'examen ») → interactive exam briefing (5 cards, format quiz) → target (incl. per-skill NCLC) → exam timing → comfort (self-rating) → section of concern → daily time → learning preference → first challenge (embedded exercise player) → route (« Évaluer mon niveau » / « Commencer mon entraînement ») → explorer name → campaign. One decision per screen; Céleste speaks in French with an English translation in English mode, and reacts to the previous answer.
- **Autosave/resume:** every answer is `PUT /api/onboarding` (table `onboarding`, migration 005) with the next step; reload resumes at that step. The challenge resumes mid-set through its own session. "Later" pauses with everything saved.
- **Challenge sets:** `defi-a` (A1–A2, self-rating 1–2) and `defi-b` (B1–B2, self-rating 3–5), context `onboarding` (evidence weight 0.1), one item per TCF section; hidden from the Practice list.
- **Completion** (`POST /api/onboarding/complete`) writes the profile (new columns: per-skill targets, exam window, plan mode, self-rating, concern, preference, route, briefing flag) and returns the **campaign** (`GET /api/campaign`): target, provisional CEFR band (self-rating ± challenge result, always a range, labelled provisional), gap ("measured after your level check"), up to 3 priorities with reasons (concern → challenge misses → speaking → others), rhythm (minutes/day, h/week over 5 days, plan mode), honest next steps.
- **Existing learners** keep their profile; Home shows "Céleste has new questions for you" until the new fields exist; `POST /api/onboarding/restart` prefills from the profile and `/bienvenue` re-runs the flow.
- **Dev tip:** `TCFQUEST_WEB_PORT`, `TCFQUEST_API_PORT` and `TCFQUEST_DB` let a throwaway test copy run beside the real app.

## Missions, notebook and reviews (milestone 4, 2026-10-16)

- **Mission format:** `context: "mission"` sets with `mission` metadata (chapter, story, objective, minutes, stage titles) and items tagged with a `stage` (A–H, blueprint Part II R9). New item kinds: `card` (story, objective, method, language, outro; read, not scored: no attempt, no XP), `multi` (checklist: all right = correct, mostly right with ≤ 1 extra = partial), and `prompt_line`/`reply` on choice items for guided dialogues.
- **Belleville** (`belleville-a2`, `belleville-b1`): the same story at two levels, an EO-T2 mission: story, objective, listening, method card (use the 2 minutes of preparation), preparation checklist, language card (polite questions), practice, a 5-turn guided phone call with M. Delaunay (with a surprise: the truck broke down), recap for Madame Roux, outro. Works without AI; real voice and AI replies replace the guided call in milestones 5–6. `/api/today` serves A2 for self-rating ≤ 2, else B1, with a reason.
- **Evidence:** choosing or arranging words in a speaking/writing item is not speaking or writing, so EO/EE keyed items count ×0.25 (flag `proxy`).
- **Mistake notebook** (`server/tcfquest/notebook.py`, migration 006): one row per item, opened on incorrect/partial, reviewed on a 1 → 3 → 7 → 14 → 30-day ladder (answers before the review date don't move it), mastered after reaching the 14-day step; wrong again re-opens from day 1. Accepted disputes delete the mistake; rejected ones show the reviewer's reason in the notebook. Page: `/carnet`; "I understand now" moves it to a 3-day review.
- **Reviews** (`server/tcfquest/reviews.py`): a virtual set `revisions` built from up to 10 due mistakes, copying items with composite ids `<set>--<item>` so Why?, disputes and the notebook find the original. Home shows a review strip when reviews are due.
- **Mastery:** per competency, p_known moves with each answer in proportion to its evidence weight; mastered at p ≥ 0.85 with ≥ 5 attempts over ≥ 2 days and at least one correct answer without help.
- **Minutes and report:** completing a set adds the time actually spent answering to `study_day`; `GET /api/sets/{id}/report` returns XP, minutes, mistakes still in the notebook and competency bars for the end-of-mission screen.
