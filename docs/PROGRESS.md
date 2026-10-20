# Progress log

Read this first when resuming. Newest entry on top.

## Accounts milestone built locally (2026-10-20, not deployed)

What was built:
- Firebase sign-in (Google, email/password with verification and reset). Code: `accounts.py`, `AccountSignIn.tsx`, `lib/account.ts`.
- An automatic Turso database per account, with an account cap and a blocked list.
- The owner's email maps to the `achraf` database.
- "Download my data" and "Sign out" in Settings.

Tests: 219 backend tests (each also run on libSQL) and 23 frontend. The sign-in screen was checked at phone size.

Live beta (https://tcf-quest.onrender.com) still runs the owner-password version.

Next: the owner creates a Firebase project and tests real sign-in on localhost; deploy only after their OK.

## Online beta B0–B1 done (2026-10-19, local only, nothing deployed)

Plan: `docs/ONLINE_BETA_PLAN.md`; details in DECISIONS (2026-10-19). Built:
- `TCFQUEST_MODE=beta`: invite codes, one database per tester, and FastAPI serving `web/dist`.
- libSQL driver adapter.
- Workers AI provider with daily caps, plus the `/api/ai/budget` endpoint.
- Pre-recorded content audio.

Tests: 210 backend tests on both SQLite and libSQL, plus 23 frontend. Browser check on a throwaway beta server (port 8790): the wrong code is refused, the right code gives a fresh onboarding per tester, and pre-recorded audio plays with the worker off.

Next, B2, needs the owner: free Cloudflare, Turso and Render accounts (no card), a Dockerfile/render.yaml, the `beta` branch with CI, and the first private deploy. Then B3: a phone and microphone pass.

## Final state (2026-10-17)

App complete against `docs/CORE_FUNCTIONAL_GAPS.md`: M1–M13, the journey road, day/night themes, vocabulary cards, dead-link guard. 195 backend + 23 frontend tests. Public repo: github.com/achrafwokei-maker/tcf-quest (clean one-commit history; the private `phase-1-foundation` branch keeps the full history). Needs the owner's own try-out: microphone and voice ratings. Possible later work: more reserved mocks, teacher-marked samples to calibrate AI scores, README screenshots.

## Next work (2026-10-17)

Gap audit approved: `docs/CORE_FUNCTIONAL_GAPS.md` is the authoritative checklist. **M1 done** (concept weaknesses + unseen retests + item metadata). **M2 done** (CEFR range + confidence per skill). **M3 done** (planner v1 on Home). **M4 done** (writing studio + AI rubric feedback). **M5 done** (speaking pipeline; real mic to be tried by the learner in Chrome/Safari). **M6 done** (EO T1–T3 with AI examiner). **M7 done** (strict exam engine + 2 weekly trials). **M8 done** (adaptive level check + report). **M9 done** (post-exam analysis + weekly focus). **M10 done** (Académie, Boîte à outils, lesson-aware planner). **M11 done** (question bank + QC). **M12 done** (full mock + section mocks). **M13 done** (12-step acceptance test + fresh-learner browser run; 182 backend tests). All core milestones M1–M13 complete. **Journey done** (one adventure with Continue my journey, 6 TCF chapters, side missions; 189 backend tests). Next: the learner tests mic + voices in his own browser; then content growth (more mocks, vocabulary cards) per `CORE_FUNCTIONAL_GAPS.md` → Remaining limits.

## Current state (2026-10-16, natural French voices)

**Voices fixed:**
- **Normaliser:** a speech normaliser (`tts_text.py`, 47 tests) means "/" is never read as "slash", and Markdown, abbreviations, prices, times and numbers are spoken naturally. The display text is unchanged.
- **Evaluation:** 16 local voices tested (Pocket TTS, Piper, macOS) for clarity (Whisper CER), accent hint, speed and licence. See `docs/VOICE_EVALUATION.md`.
- **Worker:** a new local TTS worker (port 8788, own environment `.tools/tts-eval`, `scripts/setup_tts.sh`) is started by `scripts/dev.sh`. `/api/tts` caches audio per voice and speed.
- **Characters:** each one keeps a voice (Roux/Céleste = Estelle, Delaunay = Tom, Narratrice = Siwis).
- **Voice Studio** at `/reglages`: voices per slot with previews, speed 0.8–1.2×, slow listening mode, 1–5 ratings.
- **Fallback:** the browser voice reads the normalised text and never picks Eddy/Flo.
- **Tests:** 117 backend + 17 frontend. Browser-tested the studio (previews, phone layout) and the per-character voices.
- **Waiting for:** the learner's listening ratings (target ≥ 4/5).

## Previous state (2026-10-16, milestone 4)

**Milestone 4 done:** Le Marché de Belleville as a speaking task 2 mission (A2 and B1 versions, stages B–H, method and language cards, preparation checklist, 5-turn guided call with character replies, recap, outro), mission report (XP, minutes, mistakes, competency bars), mistake notebook with spaced reviews (`/carnet`), review sessions from due mistakes, Home mission card ("Play", with reason and TCF task) and review strip, dispute results linked to the notebook, mastery tracking, study minutes, proxy evidence for keyed speaking/writing items. Tests: 65 backend (11 new) + 14 frontend. Browser-tested in a throwaway copy (temp DB on port 8788/5174, deleted after): Home card → full B1 mission with a partial checklist → report → notebook → review session. Real DB migrated to schema 6. The learner's profile has no self-rating yet (pre-dates the new onboarding), so Home offers the A2 version until he answers Céleste's new questions.

Next: milestone 5 (speaking pipeline: microphone, local Whisper transcription with confidence, typed fallback) to turn the guided call into a real spoken call.

## Previous state (2026-10-16, milestone 3)

**Milestone 3 done:** conversational onboarding with Céleste replaces the old form: guidance language, welcome, interactive TCF Canada briefing (facts from TCF_SPECIFICATION, format quiz), TCF-first target (incl. per-skill NCLC), exam timing, comfort, section of concern, daily time, preference, first TCF mini-challenge (new sets `defi-a`/`defi-b`, one item per section), route choice, explorer name, personal campaign. Autosaved per step (migration 005), resumes after reload, "Later" pause. Existing profile kept; Home banner invites the learner to answer the new questions (`/bienvenue`). Tests: 54 backend (12 new) + 14 frontend; browser-tested the whole new-learner flow in a throwaway copy (port 5174, temp DB, deleted after) incl. reload-resume, and the banner on the real app. Fixed: fast tile key presses could use a stale tile list. Next: milestone 4 (Belleville EO-T2 mission, keyed parts + mistake notebook + review strip).

## Previous state (2026-10-16, milestone 2)

**Milestone 2 done:** feedback system. All verdict looks (incl. future AI verdicts) with a tone test; "Why?" panel; report menu (too easy, too hard, unclear, dispute, technical) stored in `feedback_flag` (migration 004); disputes/technical remove evidence; review queue at `/review` (accept adds an accepted answer the checker honours, reject needs a reason and restores evidence); items-to-fix list. Tests: 42 backend (7 new) + 10 frontend. Browser-tested: wrong answer → Why? → dispute with note → review reject (reason required) → queue empty; my test data removed, the learner's set A answers kept. Next: milestone 3 (new onboarding steps 0–10 + first challenge).

## Previous state (2026-10-16, milestone 1)

**Milestone 1 done:** content format with required `tcf_target` tags (validator rejects untagged/broken content), deterministic answer checking (E.2 rules), sessions with saving, re-queue and resume, and the full-screen exercise player for select, listen, arrange and type (keyboard shortcuts, accent bar, hints, "can't listen now", feedback sheet, completion screen). Two sets: `premiers-pas-a` (A1–A2) and `premiers-pas-b` (B1–B2), reachable from Entraînement. Tests: 35 backend (10 checking, 13 content/session) + 7 frontend; browser-tested set B end to end incl. reload-resume (test data removed afterwards). Next: milestone 2 (feedback system: flags, dispute/technical, "Why?").

## Previous state (2026-10-16, night)

**Milestone 0 done:** TCF Canada facts verified on the official FEI page (via the browser pane; automated fetch is bot-blocked) and the IRCC table re-checked on canada.ca. Stored in `content/exam/tcf-canada.v1.json` and `content/exam/ircc-tcf-nclc.v1.json`, guarded by `server/tests/test_exam_config.py` (4 tests). Spec rewritten in `docs/TCF_SPECIFICATION.md`. Corrections: retake wait 20 days (not 30); writing word ranges are pass/fail. Companion name: Céleste. Next: milestone 1.

## Previous state (2026-10-16, late evening)

**Blueprint approved** (9 decisions, logged as XB1–XB9 in DECISIONS.md) with the learner's notes integrated as Part II (exam briefing, TCF-first onboarding, four-skill diagnostic, personal campaign, four skill tracks, daily template A–H, Académie TCF, speaking/writing masterclasses, Boîte à outils, Belleville as an EO-T2 mission). His notes were cut off in the Boîte à outils section; rest pending. Companion name open (Céleste or Camille). Next: milestone 0.

Earlier: Written: `docs/EXPERIENCE_BLUEPRINT.md` (onboarding, first session, screens, exercise engine, feedback, speaking, companion Céleste, progression, personalization, states, safeguards, MVP, scenarios, milestones). Waiting for his approval of the decisions listed at the end of that session. IMG-003 (avatar) prompt is logged and on hold.

## Previous state (2026-10-16, evening)

**Game-style redesign done** (Home, Journey map of France, floating tab bar, all screens restyled; light + dark). Committed on `phase-1-foundation`.

- IMG-001 (Paris hero) and IMG-002 (France map) were generated in ChatGPT (chat "Create Paris Night Illustration") but are **not in `web/public/art/` yet**; the app shows painted fallbacks until they are. When they arrive: name them `img-001-paris-hero.png` and `img-002-france-map.png`, then tune `SPOTS` in `web/src/pages/Journey.tsx` so nodes sit on the landmarks.
- Saving files from the built-in browser pane does not reach the disk, and a local upload helper was blocked by the safety classifier. The learner downloads images themselves.
- **Avatar creator done:** migration 002 (`avatar` table), `/api/avatar` (GET/PUT) and `/api/avatar/skin`; six skins (Le Voyageur A1 → Le Maître C2) unlocked only when the weakest skill's evidence-backed CEFR reaches the level; onboarding step "Votre personnage"; `/avatar` page with stage, wardrobe and the generated image prompt; Home avatar slot links to it. Tested: 8 backend + 7 frontend tests, plus a browser save (test row removed afterwards).
- Avatar art goes in `web/public/art/avatar-<skin>.png` (a1…c2); a glossy silhouette shows until then.
- Next: the learner fills in the creator at /avatar → copy the prompt into IMAGE_REQUESTS (IMG-003) → approval → generate. Then Phase 3 (Belleville mission).

## Earlier state (2026-10-16)

**Phase 1, technical foundation: done.** Phase 2 (core navigation + learner profile) is mostly done as part of it.

Branch: `phase-1-foundation` (not merged into `main` yet).

### Works and was tested

- `scripts/setup.sh`, `scripts/dev.sh`, `scripts/test.sh`.
- Project-local Python 3.12 (`.tools/`) via uv; backend packages in `server/.venv`.
- Backend (FastAPI, 127.0.0.1:8787): `/api/health` (schema version + live Ollama/model status), `/api/profile` GET/PUT with validation, `/api/summary` (XP, streak, minutes, skills, mistakes), `/api/backup`.
- SQLite schema v1 with versioned migrations (`server/tcfquest/migrations/`).
- Web app (Vite, 127.0.0.1:5173) with the "Carnet d'expédition" design system (tokens, light and dark mode, reduced motion, focus states, skip link).
- 4-step onboarding saves the profile; the app reloads into it.
- Five destinations: Aujourd'hui, Mon Aventure (interactive SVG map), Entraînement, Ma Progression, Mon Professeur IA (live local-AI status).
- Automated: 5 backend tests, 3 frontend tests, type-check, production build.
- Browser-tested: onboarding end to end, reload persistence, all tabs, dark desktop, light phone (375 px, no horizontal scroll), no console errors.

### Not built yet (shown honestly in the UI with a "Phase N" badge)

Missions, diagnostic, mistake notebook, voice, writing feedback, weekly trial, boss, simulator, reminders, profile editing.

### Next step

**Phase 3: « Le Marché de Belleville »** as the first fully working mission, with real content in `content/`: story intro, dialogue (text first, audio in Phase 4), 4 comprehension questions with verified keys, drag-the-details step, a written version of the phone message as a stand-in until voice lands, mistake tracking, completion, XP and minutes, mastery update. Then Phase 4 (voice).

### How to resume

1. `cd ~/tcf-quest && git status && git log --oneline -5`
2. `scripts/test.sh` (all should pass)
3. `scripts/dev.sh` and open http://localhost:5173
4. Continue with "Next step" above.

## History

- 2026-10-16: Natural French voices (Pocket TTS + Piper), speech normaliser, Voice Studio.
- 2026-10-16: Phase 1 foundation built and tested (see above).
- 2026-10-16: Switched to the free local plan; development approved.
- 2026-10-16: Planning documents created; project moved to ~/tcf-quest.
