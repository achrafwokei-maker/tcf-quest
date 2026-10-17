# Core functional gaps (authoritative checklist)

Audit date: 2026-10-17, against the code at commit `9196a08`. These pages give the detail, so this
checklist links to them rather than copying them:

- Exam facts: `TCF_SPECIFICATION.md` and `content/exam/*.json`
- Experience: `EXPERIENCE_BLUEPRINT.md` (Part II wins)
- Voices: `VOICE_SYSTEM.md`

Scope: **P0 and P1 only.** P2 is deferred but kept documented: the avatar and its skins, the
Journey story map, new story chapters, cosmetic rewards and cinematic effects.

Status key: ✅ DONE · 🟡 PARTIAL · ❌ MISSING · 🔧 NEEDS CORRECTION

## Done since the audit

- **M1 ✅ 2026-10-17**:
  - Weaknesses are tracked per concept (`weakness.py`, migration 007) and move through detected → training → improving → retest due → mastered, and can reopen.
  - Each one stores examples, how often and how badly it happens, how sure the diagnosis is, what practice was tried, and the retest results.
  - A retest always uses an **unseen** question on the same concept; a wrong answer on it means "rethink after 2 failures".
  - Same-day retries and hinted answers never count as proof.
  - Questions carry a difficulty, a review status and a pool; questions reserved for tests are never played or sent to the browser in training.
  - Weaknesses were rebuilt from past answers, and the notebook shows a "Weak points" section.
  - 7 tests. Still open: concepts with no unseen question show "no new question available yet" until M11 adds more questions.
- **M2 ✅ 2026-10-17**:
  - Each skill now has a CEFR range and a confidence, updated from your answers by a fixed formula, not by AI (`estimates.py`).
  - Hints, replays and speaking/writing questions answered by choosing count less; disputed or broken answers and immediate retries don't count.
  - Your self-rating gives a weak starting point, so a few lucky answers can't produce an extreme level.
  - The range narrows as evidence builds up, and every change is logged in `progress_history` (`practice`).
  - Speaking and writing stay at low confidence until real spoken and written tasks are assessed. Avatar skins need medium confidence in all four skills.
  - Estimates refresh after every answer, every flag, and at startup. 7 tests.
- **M3 ✅ 2026-10-17**:
  - Planner v1 (`planner.py`, `/api/today?minutes=`) answers what to study today, why, and what it improves.
  - Retrieval reviews and retests come first, using at most 40 % of the session.
  - Then the sets that fit the time, scored by unseen questions on your weak points, unfinished sets, priority skills, level fit (aiming for about 70–80 % success), unseen share and preparation phase.
  - Sets with nothing new are never re-proposed, and the plan fits 10, 20 or 40 minutes.
  - After 3 or more days away it's a short restart: reviews are capped at 5, with no backlog.
  - Phases overlap according to the exam date, and timed practice is noted as coming in M7.
  - Home shows the plan with a time picker; Progress shows how the estimates changed and the weak-point counts.
  - 9 tests.
- **M4 ✅ 2026-10-17**:
  - The writing studio (`/ecrit`) has 9 original tasks (3 each for T1, T2 and T3) with word ranges from the verified exam file.
  - Training mode shows a structure, phrases and things to avoid. Exam mode is a countdown with a suggested split of the 60 minutes (15/20/25), late saves are refused, and the text is auto-submitted.
  - Drafts autosave, and there's a live word count plus an "A1 non atteint" warning outside the range.
  - Feedback comes from Qwen3 using a fixed grid: 5 criteria scored 0–5, corrections marked error or style, a revised version and a level.
  - The text is scored twice to check agreement, invalid answers are retried, and every correction must quote your text.
  - Fixed rules catch common slips: elision and a/à.
  - Only errors feed weak points. The writing estimate gets low-weight AI evidence (0.2, or 0.1 if the two scorings disagree), and its confidence is capped at medium.
  - If Ollama is off, the text is saved with a "try again" option.
  - About 30 s per text. 10 tests with the AI mocked, plus one real run in the browser.
- **M5 ✅ 2026-10-17**:
  - The speaking pipeline records in the browser, converts to a 16 kHz mono WAV, and transcribes locally with MLX Whisper large-v3-turbo through the voice worker (`/transcribe`, about 0.4 s per sentence once loaded).
  - Results come with a confidence and an honest status: ok, uncertain, no speech, too short, too quiet, or engine off. Silence, noise and invented subtitle text are filtered out.
  - Recordings stay in `data/recordings` (migration 009) and can be deleted.
  - You can correct what was understood, or type instead, at any time. Confidence is shown as the machine's certainty, never as a pronunciation score.
  - `/oral` has a microphone check and repeat-after-me (which words were understood). The reusable `MicRecorder` is ready for M6.
  - 5 tests. Real-microphone capture was not tested here because the browser pane blocks microphones; everything after capture was tested.
- **M6 ✅ 2026-10-17**:
  - Speaking tasks T1–T3 with a local AI examiner (`/oral/:id`, migration 010), using timings from the verified exam file (T1 2:00; T2 2:00 preparation + 3:30; T3 4:30) enforced on the server.
  - 7 original tasks. T2 roles answer only from scenario facts kept hidden from you, always including the surprise. T3 pushes you to nuance.
  - Examiner lines are spoken in each character's voice, limited to 1–2 sentences with no Markdown, and a fixed fallback line is used when the AI is off.
  - Training mode shows the text and tips. Exam mode is listen-only (with a "can't hear" escape) and has no tips.
  - Feedback uses a fixed grid per task, is scored twice, and covers content and language only, never pronunciation.
  - Turns whose transcription is uncertain never produce grammar corrections or weak points, and they halve the evidence weight.
  - T2 shows which information you obtained. The app counts your words, turns and longest answer.
  - Corrections are trimmed to the words that changed.
  - 9 tests with the AI mocked, plus real runs of the examiner and feedback.
  - **Not done:** Belleville's guided call is still a choice-based task, not real speech (moved to M10).
- **M7 ✅ 2026-10-17**:
  - Strict exam engine (`exam.py`, migration 011, `/examen`) with 2 original weekly trials, each with 8 listening and 8 reading questions (A2→B2), plus a writing task and a speaking task, all reserved.
  - Sections run in order with server-enforced countdowns. Each recording plays once and the question appears only after it; you can't go back; there are no hints, no keys and no feedback until the end.
  - A section closes when its time is up, and writing or speaking is auto-submitted or ended. Each trial can be taken once.
  - Results show scores per section, time used, unanswered questions, a full question review with transcripts, and the writing/speaking AI feedback.
  - Exam answers count as stronger evidence (0.6), wrong answers feed weak points (not the review notebook), and estimate history is logged as `weekly`.
  - The plan shows "This week: weekly trial" when one is due (every 7 days).
  - AI scoring jobs are claimed atomically, so feedback can't run or be recorded twice.
  - The feedback prompts now ask for English, and corrections that only add a gender marker like (e) are dropped.
  - 5 tests. Browser-tested on a throwaway copy, so your trials are still unseen.
- **M8 ✅ 2026-10-17**:
  - Four-skill level check ("Bilan de niveau", about 25 min) with adaptive listening and reading: a staircase over a reserved pool of 24 questions (A1→C1), 8 served per section, starting from your self-rating.
  - It also includes one short message (writing T1) and a 2-minute interview (speaking T1).
  - The report (`report.py`, shared with the weekly trials) shows per skill: the score, where the staircase settled, the CEFR estimate and its confidence, strengths, error types found in this assessment, what it can't tell you, priorities against your CEFR goal (the NCLC target is shown separately and never converted), and the plan's next steps.
  - The report refreshes until the writing and speaking feedback is in. The campaign is marked "assessed" once the check is done, and Today invites you to take it until then.
  - "Medium" confidence now needs at least 15 full-question equivalents, so a short check alone stays "low".
  - 2 tests. Browser-tested on a throwaway copy.
  - **Limit:** with only 2–3 questions per level, the staircase can't stay at the extremes for long; M11 enlarges the pool.
- **M9 ✅ 2026-10-17**:
  - Post-exam intelligence (`analysis.py`, migration 012). Timing: ran out of time, rushed, or seconds per question.
  - Possible causes, only when the evidence supports them:
    - technique: missed implicit-meaning questions while factual questions at the same level were right;
    - French: missed questions within your estimated level, or language errors in writing/speaking;
    - timing: questions left unanswered when time ran out;
    - otherwise no cause is claimed. Causes are recorded on the weak points.
  - Retests: the weak points this assessment touched are retested on new questions.
  - Next week's focus (weakest skills plus their concepts) is stored for 7 days, and the planner adds a focus bonus with the reason "Your last assessment showed this needs work". It's updated once writing/speaking feedback is in.
  - The report shows the causes, timing, focus and retests. 4 tests.
- **M10 ✅ 2026-10-17**:
  - **Académie TCF** (`/academie`): 8 modules (CO, CE, speaking T1–T3, writing T1–T3), each going method → example → guided practice (hints) → independent practice → timed question (countdown, auto-skip) → link to the real task.
  - **Boîte à outils** (`/outils`): 12 lessons (T2 questions, T3 plan, introductions and conclusions, opposition and logical connectors, register, elision, a/à and ou/où, passé composé vs imparfait, agreement, polite conditional, time management). Each covers what, when, when not and an example, then an adaptation gap-fill and a practice question.
  - The lessons' concepts match the weak-point keys, so they're also fresh retests for errors found in writing and speaking.
  - Planner: a weak point that failed its retest twice gets a lesson first; a "technique" cause favours the Académie module; a "French" cause favours the grammar lesson.
  - Belleville's call is now a real speaking T2 task (`eo2-belleville`, with M. Delaunay and the story facts), linked from the mission's last card.
  - Generators live in `scripts/content/`. 2 tests. Browser-tested on a throwaway copy.
- **M11 ✅ 2026-10-17**:
  - Question bank: 87 reserved listening + 87 reserved reading questions (A1 7, A2 18, B1 26, B2 22, C1 12, C2 2 each), all original.
  - That covers 4 weekly trials (trial-1…4, each with reserved writing and speaking tasks), the full mock (`mock-1`: 39 + 39 with progressive difficulty, plus writing T1–T3 and speaking T1–T3), and a level check of 32 questions.
  - Quality checks (`content_qc.py`, run in the tests): answer positions balanced (≤ 45 % per position), the right option's explanation starts with "Yes", reserved questions have 4 options, no duplicates. Counts are printed with `python -m tcfquest.content_qc`.
  - Answer positions were rebalanced in the existing reserved sets (nobody had taken them).
  - Generators: `scripts/content/bank_*.py`. 2 tests.
- **M12 ✅ 2026-10-17**:
  - **Full TCF Canada mock** (`mock-full-1`): CO 39 questions / 35 min, CE 39 / 60 min, EE three tasks in one shared 60-minute block (any order, tabs), EO T1 + T2 (with preparation) + T3, for 2 h 47 in total. Timings come from the verified exam file.
  - **Section mocks** (CO, CE, EE, EO) use the same bank. Any exam that would reuse an already-answered question or task is refused and shown as "no longer unseen".
  - The planner recommends the full mock after 2 weekly trials, or when the exam is ≤ 6 weeks away (at most every 14 days).
  - Results and report combine the three writing tasks. 4 tests. Browser-checked on a throwaway copy.
- **M13 ✅ 2026-10-17**:
  - 12-step acceptance: `tests/test_acceptance.py` runs the whole journey on a fresh database (onboarding with briefing → target → level check → plan → Belleville → feedback → weak point → review → unseen retest mastered → weekly trial → report → the next plan changes).
  - Browser run as a brand-new learner (briefing, quiz, target, preferences, route, plan). Fixed what it found: the level check now comes before trials and mocks; the chapter cards are live links instead of "Phase N"; the duplicate diagnostic panel and stale notes are gone.
- **Journey ✅ 2026-10-17**:
  - One adventure (`journey.py`, `content/journey/journey.json`), presentation only: 6 chapters grouped by TCF task (Départ, Se présenter, Obtenir des informations, Raconter, Argumenter, Le Grand TCF). Weekly trials are the chapter bosses and the full mock is the finale.
  - Nodes are existing sets, lessons, writing/speaking tasks and exams.
  - Personal order inside a chapter comes from the planner's scores and the weekly focus. Nodes far below your level are marked optional, never removed.
  - Recovery side missions (reviews and retests, a lesson for a stuck weak point) are short detours, then back to the route.
  - Chapters unlock at 60 % of the previous one; bosses need the level check and the weekly rhythm.
  - One primary action, "Continuer mon parcours" (`/api/journey/continue`): it resumes the exact exam or mission in progress, otherwise takes a quick detour, otherwise goes to the next step, always with where/why/next.
  - Aventure = Continue + map + chapters (list-based, keyboard accessible). Today = Continue first, with the full plan folded.
  - Records are untouched by the journey. 7 tests.
- **Road map ✅ 2026-10-17**:
  - One reusable SVG road (`JourneyRoad.tsx`) for all 6 stages, labelled A1→C2 (difficulty aimed at, never an awarded level).
  - Seven node types (listening, reading, speaking, writing, strategy, revision, boss) and five states (done, current "you are here", recommended ★, available, locked with the reason on tap). The gold road stops at the current step.
  - Detours branch off the current checkpoint. Tapping a checkpoint opens it directly.
  - Full road on Mon Aventure, a 4-checkpoint preview on Today, and onboarding ends on the road.
  - Dead links fixed: Listening/Reading hubs (`/pratique/CO`, `/pratique/CE`), skill tiles, Professeur cards (real voice and recogniser status). No "Phase N" placeholders left.
- **Vocabulary ✅ 2026-10-17**:
  - 72 original expression cards in 9 functions tied to TCF tasks (polite requests, opinion, nuance, storytelling, cause, formal messages, phone, managing a conversation, daily life).
  - Spaced repetition (1, 2, 4, 8, 16, 32 days; at most 15 reviews and 8 new cards a day). New cards favour the tasks of your weak points and the last assessment's focus.
  - Screen: `/vocabulaire` (audio, reveal, 4 grades, keyboard 1–4). It's offered as a quick detour on the journey after the briefing.
  - It's a memory aid, self-graded: it never touches skill estimates or weak points (tested). 5 tests.
- **Quality guard ✅**: an automatic test checks that every in-app link in the code and content points at a real route (and that the guard rejects a made-up one); a backend test checks that every route the journey sends you to exists. Checked as a new learner: all 17 screens load with no errors, and 16 screens have no horizontal scroll at phone width.

## Remaining limits (honest list)

- Real-microphone capture and the natural voices need **The learner's own test** (the browser pane blocks microphones, and Claude can't hear audio). Voice ratings are still pending (target ≥ 4/5).
- Writing/speaking AI scores are unofficial and **uncalibrated**: teacher-marked samples would allow calibration.
- **One** full mock and four weekly trials: enough for about a month of weekly practice. More reserved content is needed for longer preparation (the generators in `scripts/content/` make this quick).
- P2 deferred and documented: 3D avatars, passport evolution, more story chapters, cosmetic rewards.

## Gap table (audit snapshot of 2026-10-17; see the milestones above for what changed)

| Feature | Status | Evidence | Missing / issue | Next action |
| --- | --- | --- | --- | --- |
| Verified exam facts (formats, timings, NCLC table) | ✅ | `content/exam/*.json`, `test_exam_config.py`, checked against FEI and IRCC 2026-10-16 | — | Re-check before the full mock (M12) |
| Exam orientation (briefing + quiz) | ✅ | Onboarding steps 1/1b (`Onboarding.tsx`, `onboarding.py`) | — | — |
| Target, exam date, daily time, self-rating, concern | ✅ | Migration 005, onboarding steps | — | — |
| Four-skill diagnostic | 🔧 | `defi-a`/`defi-b` have 4 items (one per section), giving a provisional band | One item per skill is not evidence. Writing and speaking are keyed proxies. No error categories or limits shown | M8 |
| Skill estimates (CEFR range + confidence) | 🔧 | `skill_profile` rows are created but **never updated** from attempts | Estimates are frozen, so avatar unlocks and the "assessed" status never move | M2 |
| Personalised roadmap / today's mission | 🟡 | `/api/today` always returns the first Belleville mission. `campaign()` ranks priorities from the concern and the challenge | Doesn't use weaknesses, the exam date, minutes, reviews or results. No phases. No adapting after missed days | M3 |
| Exercise engine (keyed types, hints, resume) | ✅ | `sessions.py`, `checking.py`, `ExercisePlayer.tsx`, tests | — | Reuse everywhere |
| Feedback (verdicts, "Why?", disputes, review queue) | ✅ | `feedback.py`, `FeedbackSheet`, `/review` | — | — |
| Mistake tracking + spaced review | 🟡 | `notebook.py`: 1/3/7/14-day schedule, reopens on regression | Tracked **per item**: the review replays the **same question** (memorised, not transferred). States are open/improving/mastered. No severity, confidence, interventions or "retest due" | M1 |
| Concept-level weakness model | 🟡 | `mastery` table: `p_known` per competency, needs several days and an unhinted answer | Not linked to mistakes. No diagnosis of the cause (French vs technique vs timing). Doesn't drive content choice | M1 |
| Question bank quality fields | 🟡 | Schema: `tcf_target`, competencies, verified keys, explanations, validator | No difficulty, review status, assessment eligibility or reserved unseen pool. Only **~51 items in total** | M1, then M11 |
| Targeted lessons (grammar, vocabulary) | ❌ | Practice tiles show "Phase N" | No lessons connected to weaknesses | M10 |
| Strategy Académie (all sections) | 🟡 | Method cards inside Belleville (EO T2 only) | Listening, reading, EO T1/T3 and EE T1–T3 strategies are all missing. No explain→example→guided→independent→timed sequence | M10 |
| Language toolbox (frameworks, connectors, register) | 🟡 | Belleville "language" cards (T2 question forms) | Library and "when not to use" missing. No adaptation exercises | M10 |
| Speaking practice EO T1–T3 (mic, STT, timing, AI examiner) | ❌ | Voices done (`tts.py`). MLX Whisper is installed only for evaluation | No recording, transcription, task timers, examiner or rubric feedback | M5, M6 |
| Writing practice EE T1–T3 (timer, word count, drafts, feedback) | ❌ | Only short `type` items | Whole writing studio and rubric feedback missing | M4 |
| AI rubric feedback (Ollama, labelled estimate) | ❌ | `ai.py` only checks status | No prompts, rubrics, double scoring or graceful fallback | M4 (shared by M6) |
| French audio (natural TTS, normalisation) | ✅ | `tts_text.py`, worker, Voice Studio, 52 tests | Human ratings pending (≥ 4/5) | The learner rates the voices |
| Strict exam mode engine | ❌ | — | Timers, no hints, one play, timeout, saved submissions, sequencing | M7 |
| Weekly four-skill trial | ❌ | Placeholder only | — | M7 |
| Post-exam intelligence report → roadmap | ❌ | Mission report shows XP, minutes and competencies, but not an exam report | Report doesn't exist and doesn't feed weaknesses or the roadmap | M9 |
| Full section mock / full TCF mock (2 h 47) | ❌ | — | Needs a bank of ≥ 39+39 unseen listening/reading items plus writing/speaking tasks | M12 |
| Progress view (target, 4 skills, trends, milestones) | 🟡 | `Progress.tsx`, `/api/summary` | Shows frozen estimates. No trends, upcoming trial or milestones | M3 |
| Scales never mixed; "estimate" labels | ✅ | Product rules, labels in the UI | Check again when estimates start moving (M2) | — |
| Learner data saved locally + backup | ✅ | SQLite migrations 001–006, `/api/backup` | — | — |

## Learner-flow check (12 steps)

| # | Step | Result |
| --- | --- | --- |
| 1 | Discover the TCF format | ✅ |
| 2 | Set a target | ✅ |
| 3 | Complete a diagnostic | ✅ M8 |
| 4 | Personalised roadmap | ✅ M3 |
| 5 | TCF-specific mission | ✅ Belleville (EO T2, now also real speech) |
| 6 | Feedback | ✅ |
| 7 | Weakness recorded | ✅ M1 |
| 8 | Corrective practice | ✅ M1/M3 |
| 9 | Improve on an unseen task | ✅ M1 retests (limited by bank size until M11) |
| 10 | Weekly timed assessment | ✅ M7 |
| 11 | Diagnostic report | ✅ M8/M9 |
| 12 | Next roadmap adapts | ✅ M3/M9 |

## Milestones (build in order; each one ends tested and committed)

Numbering restarts after the milestones already done (0–4 and voices).

| # | Objective | Reuse | Changes | Depends on | Acceptance and tests |
| --- | --- | --- | --- | --- | --- |
| **M1** | **Weakness model + question-bank metadata** | `mastery`, `notebook`, `content` validator | <ul><li>Item fields: `difficulty` (1–5), `review_status` (draft / reviewed), `pool` (training / assessment).</li><li>New `weakness` table keyed by competency: skill, task, category, examples, frequency, severity, confidence, interventions, last seen, retest results.</li><li>States: detected → training → improving → retest due → mastered, and reopen.</li><li>Item mistakes feed weaknesses.</li><li>A retest picks an **unseen sibling item** with the same competency.</li></ul> | — | <ul><li>Unit tests for the state machine and reopening.</li><li>A retest never reuses the failed item.</li><li>Assessment-pool items never appear in training.</li></ul> |
| **M2** | **Evidence → skill estimates** | `attempt.evidence_weight`, exam config | <ul><li>Deterministic update of `skill_profile` (CEFR range + confidence) from weighted attempts.</li><li>Disputed attempts are excluded.</li></ul> | M1 | <ul><li>Fixture tests: strong or weak runs move the range.</li><li>Proxy-only evidence keeps confidence "low".</li></ul> |
| **M3** | **Planner v1 (today's mission + reason)** | `/api/today`, `campaign()` | <ul><li>Score candidate activities by weakness severity, reviews due, exam date, daily minutes and phase.</li><li>Fit the plan to the time available.</li><li>Missed days: no backlog (review cap kept).</li><li>Progress page shows trends and the next trial.</li></ul> | M1, M2 | <ul><li>The next mission changes after weak or strong fixtures.</li><li>The plan fits 10, 20 and 40 minutes.</li></ul> |
| **M4** | **Writing studio EE T1–T3 + AI rubric feedback** | Exercise player shell, exam config word ranges, `ai.py` | <ul><li>Editor with timer, word count and draft autosave.</li><li>Training mode (templates) vs exam mode.</li><li>Rubric prompts to Qwen3.</li><li>JSON scoring done twice, plus an agreement check.</li><li>Labelled "unofficial estimate".</li><li>Corrections feed M1.</li></ul> | M1 | <ul><li>Word-range rules tested.</li><li>Ollama off → saved, with feedback "pending".</li><li>Rubric JSON validated.</li></ul> |
| **M5** | **Speaking pipeline** | MLX Whisper (already installed), the TTS worker | <ul><li>Microphone permission and recording.</li><li>Local transcription with confidence.</li><li>Empty / noise / uncertain cases.</li><li>Typed fallback.</li><li>Recordings stay in `data/`.</li></ul> | — | <ul><li>Transcription tests on generated clips.</li><li>No penalty when confidence is low.</li></ul> |
| **M6** | **EO T1–T3 with the AI examiner** | M4 rubric engine, TTS characters | <ul><li>Task timers (T1 2 min; T2 5 min 30 with 2 min prep; T3 4 min 30).</li><li>The examiner speaks in short lines.</li><li>Feedback on content and language only (no pronunciation score).</li><li>History saved and redo allowed.</li><li>Belleville's guided call becomes real speech.</li></ul> | M4, M5 | <ul><li>Timer and turn tests.</li><li>Speech-recognition doubt never becomes a pronunciation penalty.</li></ul> |
| **M7** | **Strict exam engine + weekly trial** | Player, M4/M6 | <ul><li>Exam mode: plain UI, accurate timers, one play, no hints or corrections, timeout auto-submit, saved answers.</li><li>Weekly trial: a short set from all four skills, using the assessment pool, labelled "partial simulation".</li></ul> | M1, M4, M6 | <ul><li>Timeout, one-play and resume-after-reload tests.</li><li>No feedback before the end.</li></ul> |
| **M8** | **Real four-skill diagnostic + report** | `defi-*`, M2, M4, M6 | <ul><li>Adaptive listening/reading (about 8–10 items each).</li><li>Short EE T1 and EO T1.</li><li>Report: ranges, strengths, error categories, evidence limits, priorities.</li><li>The initial roadmap is set.</li></ul> | M2–M7 | <ul><li>Report fixtures.</li><li>Labelled "not an official result".</li></ul> |
| **M9** | **Post-exam report → weaknesses → roadmap** | M1, M3, M7 | <ul><li>Per-skill and per-task analysis, timing problems, root-cause hints (French vs technique vs timing, only with enough evidence).</li><li>Required retests.</li><li>The planner reweights next week.</li></ul> | M7 | Fixture: a weak trial → next week's plan changes. |
| **M10** | **Académie + Boîte à outils + targeted lessons** | Card items, competencies | <ul><li>A strategy sequence per section and task (explain → example → guided → independent → timed → review).</li><li>A toolbox library (when / when not, adaptation exercise).</li><li>Lessons linked to weakness categories.</li></ul> | M1, M3 | <ul><li>Each card has practice items.</li><li>The planner can assign them.</li></ul> |
| **M11** | **Bank scale-up (P1)** | Validator, TTS | <ul><li>Original listening/reading items across levels, quality-reviewed.</li><li>An assessment pool large enough for 4 weekly trials plus 1 full mock.</li></ul> | M1 | The validator passes; counts per section, level and pool are reported. |
| **M12** | **Full section mock + full mock (P1)** | M7 | <ul><li>39/35 min, 39/60 min, writing 60 min, speaking ~12 min, in the official order.</li><li>Report via M9.</li></ul> | M7, M9, M11 | Timing test against `tcf-canada.v1.json`. |
| **M13** | **12-step learner-flow acceptance run** | — | Browser run on a fresh database | All | All 12 steps ✅ |

## Research status

- **Exam facts:** verified 2026-10-16. Nothing to redo until M12.
- **Learning methods:** already set in `LEARNING_SYSTEM.md` (spaced retrieval, mastery over several days, hint penalties).
- **Competitor comparison:** not needed to close these gaps. Optional before M10.
