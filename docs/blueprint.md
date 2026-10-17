# TCF QUEST — Product Strategy & Development Blueprint

Oct 16, 2026 · the learner · Planning phase, no code

## 0. Exam facts this plan is built on

The reference format in your brief is correct: 39 + 39 questions, 35 + 60 minutes, 3 writing tasks in 60 minutes, 3 speaking tasks in about 12 minutes. The IRCC score table below was checked on canada.ca today. The France Éducation international (FEI) page blocked automated access, so task details come from consistent secondary sources and must be re-checked against the FEI candidate handbook before content production starts.

| Section | Format | Duration | Score scale | Confidence |
| --- | --- | --- | --- | --- |
| Compréhension orale | 39 MCQ, increasing difficulty, each recording played once | 35 min | 331–699 (NCLC band) | High (secondary, consistent) |
| Compréhension écrite | 39 MCQ, increasing difficulty | 60 min | 331–699 | High (secondary, consistent) |
| Expression écrite | T1 message 60–120 words; T2 article/letter 120–150 words; T3 compare two documents then give opinion, 120–180 words (40–60 + 80–120) | 60 min | 0–20 | Medium: word counts vary across sources |
| Expression orale | T1 directed interview \~2 min, no prep; T2 interaction 5 min 30 incl. 2 min prep; T3 point of view 4 min 30, no prep | \~12 min | 0–20 | Medium |

**IRCC TCF Canada → NCLC table** ([canada.ca, checked 2026-10-16](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/standard-requirements/language-requirements/test-equivalency-charts.html))

| NCLC | Reading | Listening | Writing | Speaking |
| --- | --- | --- | --- | --- |
| 10 | 549–699 | 549–699 | 16–20 | 16–20 |
| 9 | 524–548 | 523–548 | 14–15 | 14–15 |
| 8 | 499–523 | 503–522 | 12–13 | 12–13 |
| 7 | 453–498 | 458–502 | 10–11 | 10–11 |
| 6 | 406–452 | 398–457 | 7–9 | 7–9 |
| 5 | 375–405 | 369–397 | 6 | 6 |
| 4 | 342–374 | 331–368 | 4–5 | 4–5 |

**What this means for the product**

- Three scales must never be mixed: CEFR level (A1–C2, general ability), TCF score (331–699 or 0–20 per skill), and NCLC (4–10+, immigration). The app shows all three, labelled, and always marked as estimates.
- NCLC 10 needs only 16/20 in speaking and writing and 549+ in comprehension. That is roughly C1, not C2. For Express Entry points, C2 adds nothing over NCLC 10, so C2 is a personal goal, not an exam goal.
- The score table is the one thing most likely to change. It lives in a versioned config, never hard-coded.

**Still unverified (check before Phase 2):** exact word limits per writing task; whether speaking T2 prep is 2 minutes in all centres; retake waiting period (commonly cited as 30 days); whether results stay valid 2 years for IRCC (commonly cited, not checked today). Secondary sources used: [tcfca.com](https://www.tcfca.com/tcf-canada/), [tcfcanadaformation.com](https://tcfcanadaformation.com/tcf-canada/epreuves).

## 1. What we are building

TCF QUEST is a personal French coach that measures each of the four TCF skills separately, decides what you should do today, and proves progress with exam-style evidence. The adventure layer is the wrapper that makes daily practice feel like progress, not the engine.

- **Problem.** Adults preparing for TCF Canada juggle generic apps (no exam format), PDF mock tests (no feedback), and expensive tutors (no daily structure). Nobody tells them which skill is costing them NCLC points this week.
- **User.** First and foremost you: an adult targeting NCLC 7+ for Express Entry, with C1/C2 as a long-term goal. Later, other TCF Canada candidates with the same need.
- **Solution.** Diagnose per skill → build a plan weighted toward the weakest skill → deliver short daily missions → re-measure weekly under exam conditions → adjust the plan.
- **Differentiators**, in order of value:
  1. Exam-faithful TCF Canada simulator with honest NCLC estimates and a confidence range.
  2. Speaking and writing practice on the real task types, with rubric-based AI feedback.
  3. A persistent learner model (error notebook + mastery map) that the tutor actually uses.
  4. Mastery-gated progression, so the map reflects real ability.
  5. Premium adult design that respects your time.

## 2. Critical evaluation

The vision is strong, but as written it is three products (a course, an exam simulator, an AI tutor) plus a game. Built in that order it would take a year before it helps you pass. The fix is to build the measurement and practice core first and let the story grow around it.

**What is strong**

- Per-skill levels instead of one global level. This matches how the TCF and NCLC actually score.
- Mastery-gated unlocks and “never claim official scores”. These protect the app from lying to you.
- Training mode vs Exam mode. This is exactly how serious prep works.
- A persistent learner profile. This is what separates a tutor from a chatbot.

**What is missing**

- **A clear target metric.** Express Entry cares about NCLC per skill, and the lowest skill limits eligibility. The headline number on Home should be “weakest skill vs. NCLC 7 (or your target)”, not XP.
- **Exam strategy training.** Pacing (about 54 s per listening item, 92 s per reading item), answering every MCQ, and planning writing time are worth points on their own.
- **Speaking and listening volume.** These skills need hours of input and output. Lessons alone will not move them; the app needs a daily listening habit and frequent short speaking reps.
- **Content supply plan.** The hardest part is not code but hundreds of good, calibrated questions with natural French audio.
- **A calibration plan.** AI scores mean nothing until compared with real results (your own official score, or human-marked samples).

**What I would change**

| Your idea | Concern | Proposal |
| --- | --- | --- |
| Full A1–C2 course in chapters | Huge content load; most of it is not on your exam path | Start at your diagnosed level. Chapters cover the gap from there to NCLC 7–9 first; C1/C2 content comes later. |
| Five-tab navigation with a separate AI Tutor tab | A chat tab becomes a dead end. The tutor is most useful inside an exercise. | Four tabs (Today, Journey, Practice, Progress). The tutor is a button available on every screen and inside every correction. |
| Weekly trial every week | A full trial is 2h45 and noisy week to week | Weekly: a 25–40 min mini-trial. Full simulation every 3–4 weeks and before the exam. |
| Rich story and cinematic world | Expensive art, and it can feel childish or slow | A restrained “expedition journal” style: one illustrated map, chapter cards, subtle motion. Story text is itself French reading practice at your level. |
| AI generates exercises freely | Quality drifts; wrong answers get taught | AI drafts, a human (or a second model plus rules) reviews, then the item is calibrated before it counts toward scores. |

**What could become complicated:** real-time voice conversation, pronunciation scoring at phoneme level, full item-response-theory calibration, social features, and native apps for both stores. All are worth having later; none are needed for the MVP.

**Assumptions to validate early**

1. AI writing and speaking scores land within ±2 points (of 20) of a qualified human marker on most samples.
2. Synthetic French audio is good enough for listening practice, or we need recorded human audio.
3. You will use it daily for 20–45 minutes, and the habit survives week 3.
4. Short mini-trials predict full-simulation scores well enough to guide the plan.

**What makes it genuinely effective for the TCF:** exam-format task types from day one, timed practice, error-driven revision, lots of graded speaking and writing, and honest score ranges.

## 3. The ideal experience, first launch to exam day

The learner should always see three things: today's mission, why it was chosen, and the distance to target. Everything below serves that.

1. **Awakening (day 1, \~10 min + diagnostic).** A calm intro, then four questions: target NCLC, exam date (or “not booked”), minutes per day, and which skill feels weakest. Then the diagnostic.
2. **Diagnostic (\~60–75 min, can be split across two sittings).** Adaptive listening and reading blocks (about 15 items each), one short writing task, one speaking task, and a 10-minute grammar/vocabulary probe. Each skill result is shown as a range (for example “Speaking: A2+ to B1, low confidence”).
3. **Campaign reveal.** A map with your four skills plotted against the target, the chapter you start in, and the plan: this month's goal, this week's focus, today's first mission. One sentence explains each priority (“Speaking is 2 levels below target and limits your NCLC”).
4. **Daily mission (15, 30 or 45 min).** Warm-up from the error notebook → micro-lesson on today's focus → targeted drills → one TCF-format task → feedback → reward and tomorrow's preview. Missing a day shrinks tomorrow's plan instead of shaming you.
5. **Weekly trial (Sunday, 25–40 min).** Timed, mixed-skill, no hints. Report: estimates per skill with ranges, change vs last week, top 3 recurring errors, pacing, next week's focus. The plan updates automatically and shows what changed.
6. **Checkpoints and boss.** Each chapter has 3–5 checkpoints and a boss that tests the chapter's competencies in exam format. Failing produces a recovery path and a new question set, never the same questions.
7. **Full simulation (every 3–4 weeks, and in the final 4 weeks weekly).** Exact timings and rules, then a detailed report with an estimated NCLC range per skill.
8. **Exam countdown (last 14 days).** The plan switches to review mode: simulations, pacing drills, writing templates, speaking warm-ups, rest day before the exam.
9. **After the exam.** You enter your official scores. The app compares them with its estimates and recalibrates. This is also how the AI scoring gets validated.

## 4. Architecture and data model

In plain terms: a content library holds reviewed questions and lessons; an assessment engine scores what you do; a learner model remembers what you know; a planner (plain rules, not AI) decides what comes next; and the AI tutor explains, corrects and converses using the learner model as context. AI never decides your level on its own.

**Systems**

| System | Job | Deterministic or AI |
| --- | --- | --- |
| Profile & goals | Target NCLC, exam date, time budget, preferences | Deterministic |
| Content library | Lessons, items (MCQ, writing and speaking prompts), audio, difficulty tags, CEFR level, skill and grammar tags, review status | Deterministic store; AI only drafts |
| Assessment engine | Scores MCQs, times sections, enforces exam-mode rules, computes skill estimates with ranges | Deterministic |
| Productive-skill scorer | Rates writing and speaking on a TCF-style rubric (task completion, coherence, range, accuracy) | AI, constrained by rubric, with consistency checks |
| Learner model | Skill estimates, per-competency mastery, error notebook, spaced-repetition schedule, history | Deterministic math; AI tags error types |
| Planner | Builds monthly / weekly / daily plans from gaps and time budget | Deterministic rules |
| AI tutor | Explanations, corrections, conversation, examiner role-play, exercise drafts | AI, given learner-model context |
| Speech pipeline | Record → transcribe → score; text-to-speech for prompts and listening | Third-party services |
| Progression | Chapters, checkpoints, bosses, unlocks, achievements | Deterministic, driven by mastery |
| Notifications | Daily reminder, streak-safe nudges, trial day | Deterministic |

**How a single exercise flows:** the planner picks an item → you answer → the assessment engine scores it (or the AI scorer, for writing and speaking) → errors are tagged and stored in the notebook → mastery and the review schedule update → the planner uses the new state tomorrow.

**Conceptual data model**

| Entity | Key fields | Relates to |
| --- | --- | --- |
| User | goals, target NCLC, exam date, daily minutes, locale | has one SkillProfile, many Attempts |
| SkillProfile | per skill: CEFR estimate, TCF-scale estimate, NCLC estimate, low/high bound, confidence, updated\_at | snapshots in ProgressHistory |
| Competency | id, skill, CEFR level, description (e.g. “subjonctif after expressions of will”) | tagged on Items and Mistakes |
| Mastery | user, competency, probability known, evidence count, last seen, next review | drives Planner and unlocks |
| Lesson | competency, level, content blocks, audio | contains Items |
| Item | skill, task type, prompt, media, options, answer, difficulty, discrimination, review status, version | used in Attempts and Assessments |
| Assessment | type (diagnostic, checkpoint, boss, weekly, full sim), item list, rules, timing | many Attempts |
| Attempt | user, item, response (text, choice, audio ref), score, time taken, mode | yields Feedback, Mistakes |
| Feedback | attempt, rubric scores, comments, corrections, model + prompt version, confidence | audited later |
| Mistake | user, competency, error type, example, count, last seen, resolved | feeds revision |
| StudyPlan | user, period (month/week/day), objectives, generated items, rationale | regenerated after trials |
| Chapter / Checkpoint | order, required competencies, boss assessment | unlock state per user |
| Achievement | criteria, earned\_at | user |
| ScoreConfig | version, TCF→NCLC table, effective date | used by every estimate |

Two rules keep this honest: every AI output stores its model and prompt version, and every estimate is recomputed from raw Attempts so a better scoring method can be re-run on old data.

## 5. Screens

I recommend four tabs (Today, Journey, Practice, Progress) plus a tutor button present everywhere. The table lists every major screen; “MVP” marks what version 1 needs.

| Screen | Purpose and what you see | What you can do | Data needed | What makes it engaging | MVP |
| --- | --- | --- | --- | --- | --- |
| Welcome | Calm title card, one-line promise | Start, sign in | none | Short, cinematic fade into the map | Yes |
| Goal setup (4 steps) | Target NCLC, exam date, daily minutes, self-rated weakest skill | Pick, skip date | Score table | Shows what NCLC 7 vs 9 means for points | Yes |
| Diagnostic hub | Four skill tiles + grammar probe, progress, time estimate | Start any block, pause, resume | Diagnostic item pool | Each completed block lights a region of the map | Yes |
| Diagnostic test runner | One item at a time, timer, audio player | Answer, flag, continue | Items, media | Clean focus mode | Yes |
| Writing / speaking task | Prompt, word counter or record button, timer | Write, record, re-record (training only) | Prompt, rubric | Live word count vs limits | Yes |
| Diagnostic results | Four skill bars with ranges, target line, top 3 weaknesses | See details, view plan | SkillProfile | Honest ranges explained in one sentence | Yes |
| Campaign reveal | Map, starting chapter, month/week goals | Accept, adjust time budget | StudyPlan | Map animates to your start point | Yes |
| **Today** (home) | Mission card with length switch (15/30/45), why it was chosen, readiness meter, streak | Start mission, swap a step, quick review | Plan, Mastery, Mistakes | One clear next action | Yes |
| Mission player | Steps: review → lesson → drills → TCF task → feedback | Answer, ask tutor, skip with reason | Items, Lessons | Step progress bar, small satisfying confirmations | Yes |
| Feedback / correction | Your answer, corrected version, rubric scores, explanation, errors added to notebook | Ask tutor “why”, retry, save example | Feedback | Diff view of your text vs corrected | Yes |
| Mission complete | What improved, XP, mastery changes, tomorrow preview | Continue or stop | Mastery delta | Shows real skill movement, not only points | Yes |
| **Journey** map | Chapters as regions, checkpoints, boss gates, your position | Open chapter, view requirements | Chapters, unlock state | Illustrated expedition map, subtle motion | v1 simple |
| Chapter detail | Competencies, checkpoint list, boss requirements | Start checkpoint, review | Competencies, Mastery | Story vignette in French at your level | v1 simple |
| Boss intro / result | Stakes, format, timing; then pass/fail, why, recovery missions | Start, retry later | Assessment | Gate opens on pass | Yes |
| **Practice** hub | Four skills + Simulator + Error notebook | Pick skill, task type, mode | Item pool | Recommended badge on weakest skill | Yes |
| Skill practice list | Task types by TCF section (e.g. writing T1/T2/T3) | Choose training or exam mode | Items | Personal best per task | Yes |
| Simulator lobby | Full or section simulation, rules, timings, quiet-room checklist | Start | Assessment config | Feels like exam day | Yes |
| Exam-mode runner | Official-style timings, single audio play, no hints | Answer, navigate within rules | Items | Faithful conditions | Yes |
| Simulation report | Per-skill estimate with range, NCLC estimate, pacing, item review | Review answers, add to plan | Attempts | “Estimate, not official” label on every number | Yes |
| Error notebook | Recurring mistakes grouped by competency, with examples | Drill this error, mark understood | Mistakes | Errors shrink as you fix them | Yes |
| **Progress** dashboard | Skill trends, readiness, time studied, milestones | Change range, open report | ProgressHistory | Trend vs target line | Yes |
| Weekly report | Changes since last week, recurring errors, next week's focus | Accept plan, adjust | Weekly trial | One-paragraph coach summary | Yes |
| Tutor panel (overlay) | Chat with context of current screen | Ask, request examples, role-play | Learner model | Knows what you just got wrong | v1 basic |
| Speaking studio | Examiner role-play for speaking T1–T3 | Talk, get transcript and feedback | Speech pipeline | Realistic examiner voice | v2 live; v1 record-and-score |
| Settings & privacy | Reminders, data export, delete recordings | Change, export, delete | User | Clear control | Yes |
| Official result entry | Enter your real TCF scores | Save | ScoreConfig | Closes the loop | v1 |

**States to design up front:** loading while AI scores (show a progress line and “usually under 20 seconds”, let the learner keep reading); offline (practise cached items, queue uploads); AI failure (save the attempt, retry later, never lose writing); empty states (first day, no errors yet); failure (boss failed → explain and route to recovery). **Accessibility:** dynamic text size, captions and transcripts after listening practice (not during exam mode), full keyboard and screen-reader support, no colour-only meaning, reduced-motion setting.

## 6. Learning, assessment and gamification

The rule: rules decide, AI explains. Levels, unlocks and plans come from transparent calculations over evidence; AI supplies feedback, error tags and conversation.

### Adaptive learning

- **Priority score per skill** = gap to target (in NCLC steps) × weight for “this is your lowest skill” + small weight for time since last practised. The weakest skill gets about 40% of weekly time, the others share the rest, and no skill drops below 10%.
- **Mastery per competency** uses a simple Bayesian knowledge-tracing style update: each correct or incorrect attempt moves the probability that you know it. A competency counts as mastered at ≥ 0.85 with at least 5 attempts across 2 separate days.
- **Spaced repetition** (FSRS or SM-2 style) schedules review of vocabulary, mistakes and mastered competencies so they are re-tested before they fade.
- **Difficulty** targets about 70–80% success in training. Two sessions above 85% raise difficulty; two below 60% lower it.
- **Avoiding overestimation:** estimates use only exam-mode or no-hint attempts; ranges widen with little evidence; a skill level is only raised after the evidence holds on a second occasion; hints and retries count as weaker evidence.
- **Weekly update:** the trial result replaces the skill estimate, the planner reweights skills, and the three most frequent error types become next week's micro-lessons.

**Example learner (you, hypothetically).** Diagnostic: reading B2 (≈ NCLC 8), listening B1+ (≈ NCLC 6–7), writing B1 (≈ 9/20), speaking A2+ (≈ 6/20, low confidence). Target NCLC 7 everywhere in 12 weeks. Plan: speaking 40%, writing 25%, listening 25%, reading 10%. Week 1 errors: passé composé auxiliaries, missing connectors, « il y a / depuis ». Daily 30-min mission: 5 min error review, 5 min connector lesson, 8 min drills, 10 min speaking T2 practice, feedback. Week 4 trial: speaking rises to 8/20 (range 7–9), writing to 10/20; listening flat. Planner shifts listening to 30%, adds a daily 10-min listening block. Week 8 full simulation: all four skills in the NCLC 7 range, speaking still the lowest; plan shifts to exam-timed practice and speaking T3 argument structure.

### Assessment system

| Assessment | When | Length | Purpose | Counts toward estimate |
| --- | --- | --- | --- | --- |
| Diagnostic | Day 1, then on request every 3 months | 60–75 min | Starting level per skill with range | Yes |
| Mission task | Daily | 5–12 min | Practice + feedback | Weakly (training mode) |
| Checkpoint | 3–5 per chapter | 10–15 min | Confirm chapter competencies | Mastery only |
| Boss | End of chapter | 30–45 min | Gate to next chapter | Yes |
| Weekly trial | Weekly | 25–40 min | Trend and plan update | Yes |
| Full simulation | Every 3–4 weeks; weekly in last month | \~2h45 | Exam readiness | Yes, highest weight |

- **Comprehension scoring.** Each item carries a difficulty and discrimination value. MVP: items hand-placed on a CEFR difficulty scale and mapped to the 331–699 band by a transparent lookup, then refined. Later: a proper item-response model calibrated on real response data.
- **Writing and speaking scoring.** The AI scores against a published rubric per task (task achievement, coherence, lexical range, grammatical control, plus pronunciation and fluency for speaking). It scores twice with different prompts; if the two disagree by more than 2 points, the result is shown as low confidence. Calibration: a set of 30–50 human-marked samples per task, and your official score when you get it.
- **Content validation.** Every item goes through: draft (AI or human) → automatic checks (one correct answer, no ambiguity, level-appropriate vocabulary) → human review by a qualified French teacher → pilot (collect answers) → retire items that behave badly.
- **Exam-format accuracy.** All timings and task definitions live in one versioned exam config, reviewed against official FEI material every quarter.
- **Wording rule.** Every estimate reads “Estimated NCLC 7 (likely 6–8). Not an official TCF result.”

### Gamification and story

The world is **The French Expedition**: you are mapping a French-speaking world, region by region, and each region is a chapter. The map shows what you can genuinely do.

- **Chapters** (renamed to fit an exam-first path): 1 Le Premier Pas (A1–A2 foundations), 2 La Vie Quotidienne (A2–B1), 3 La Cité des Idées (B1–B2, opinions, NCLC 6–7), 4 Le Labyrinthe des Arguments (B2–C1, NCLC 8–9), 5 La Maîtrise (C1–C2, NCLC 10+). You start in the chapter your diagnostic places you in; earlier chapters show as “charted” with an optional review.
- **Progression** is mastery-gated: a boss unlocks when the chapter's competencies are at mastery, and passing it opens the next region. XP exists for motivation only and never unlocks content.
- **Bosses** are exam-format tests with a theme (« Le Conseil municipal » debate for speaking T3, for instance). Failing gives a short diagnosis and 3–5 recovery missions; the retry uses different items.
- **Rewards** that mean something: journal entries in French unlocked by progress, achievements tied to real behaviour (first full simulation, 30 speaking tasks, an error type eliminated), and a streak that allows rest days.
- **Story as learning.** Each chapter's narrative is short reading and listening material at the chapter's level, so story time is study time.
- **Guardrails:** no leaderboards in MVP, no loss of progress for missed days, and the game layer never hides the actual estimates.

## 7. Technology stack

Recommendation: one TypeScript codebase in Expo (React Native) for iOS, Android and web, on Supabase (Postgres, auth, file storage, server functions), with Claude for tutoring and scoring and a dedicated speech service. It is boring, cheap at small scale, and one developer can maintain it. Prices below are approximate and must be re-checked before committing.

| Area | Options considered | Recommendation | Why / tradeoff |
| --- | --- | --- | --- |
| Frontend | Expo (React Native); Flutter; PWA (Next.js) | **Expo + TypeScript** | One codebase for phone and web, reliable microphone recording and push, easy store release later. A PWA is cheaper but iOS audio and notifications are weaker. Flutter is fine but splits the language from the backend. |
| Backend | Supabase Edge Functions; Node API on Fly/Render; Firebase | **Supabase functions**, move heavy jobs to a small Node worker if needed | Little server code to own. Firebase's document store fits learner analytics worse than SQL. |
| Database | Postgres; Firestore; MongoDB | **Postgres (Supabase)** | Relational data (attempts, items, mastery) and analytics queries. |
| Auth | Supabase Auth; Clerk; Firebase Auth | **Supabase Auth** (email + Apple/Google) | Included; Clerk is nicer but another vendor. |
| AI models | Claude; OpenAI; Gemini; open models | **Claude**: a top model for writing/speaking feedback and tutoring, a small fast model for tagging and drills | Strong French and long-context reasoning; route by task to control cost. Keep an abstraction layer so models can be swapped. |
| Speech-to-text | Azure Speech; Whisper-class API; Deepgram; Google | **Azure Speech** for scoring (it offers pronunciation assessment for French), Whisper-class as fallback | Pronunciation assessment is the hard part; verify fr-FR/fr-CA support and quality in a spike. |
| Text-to-speech | Azure neural voices; ElevenLabs; Google | **Pre-generate** listening audio with a high-quality TTS, plus human recordings for exam-style items | Live TTS only for tutor replies. Mix France and Canadian accents. |
| Audio | expo-audio; native modules | **expo-audio**, compressed upload to storage | Store recordings privately, auto-delete after a set period. |
| Notifications | Expo push; OneSignal | **Expo push** | Free and enough for reminders. |
| Hosting / deploy | Supabase cloud; Vercel for web; EAS for app builds | **Supabase + EAS** | Managed, low ops. |
| Analytics / monitoring | PostHog; Amplitude; Sentry | **PostHog + Sentry** | Product funnels and errors; both have free tiers. |

**Ongoing cost, rough order of magnitude for one daily learner:** hosting free tier to about US$25/month; AI feedback and tutoring roughly US$5–30/month depending on how much speaking and long feedback is used; speech services a few dollars per hour of audio. At scale the AI and speech bill dominates, so pricing must be checked and per-user budgets enforced before any public launch.

**Limitations:** pronunciation scoring is useful as practice feedback, not as exam prediction; real-time voice conversation adds latency and cost and is deferred to v2; store release needs privacy policies and review time.

## 8. MVP definition

The MVP is a single-learner TCF Canada trainer that you can use daily within about 8–12 weeks of starting development: diagnostic, daily missions, writing and speaking feedback, a weekly mini-trial, one full simulation, and an error notebook. The story is present but light.

**Version 1 (essential)**

- Onboarding with goals and the score table.
- Diagnostic for all four skills with ranges.
- Rule-based planner: weekly focus and a 15/30/45-minute daily mission.
- Item bank: about 300 listening and 300 reading items across A2–C1, 20 prompts per writing task type, 20 per speaking task type.
- Writing feedback (rubric + corrections) and record-then-score speaking feedback.
- Error notebook with spaced review.
- Weekly mini-trial and weekly report.
- One complete exam-mode simulation (two forms if content allows).
- Progress dashboard with CEFR / TCF / NCLC estimates and ranges.
- Simple map with 5 chapters, checkpoints and bosses for chapters 2–4 (your likely range).
- Tutor overlay (text) with learner context.
- Privacy basics: recording deletion, data export.

**Version 2**

- Live spoken examiner role-play.
- Pronunciation drills with phoneme feedback.
- Item-response calibration from collected data; more simulation forms.
- Richer story, illustrated journal, achievements.
- Monthly plans and exam countdown mode.
- Public release: accounts for other learners, onboarding polish, payments.

**Later**

- Chapter 5 C1/C2 content, DALF-style depth.
- Human-marker marketplace for calibrated scoring.
- Community features, study groups.
- Teacher dashboard.
- Offline-first full mode.

**The real cost is content, not code.** Writing, reviewing and recording \~600 comprehension items is roughly 150–300 hours of work even with AI drafting. A qualified French teacher reviewing 20–40 hours is the single best use of money in the MVP.

## 9. Phased roadmap

Six phases take the project from approved plan to a validated MVP in roughly 12–20 weeks. Assumptions: you plus Claude building, about 15–20 hours a week, a paid French teacher for review, and no store release before Phase 5. Each phase ends at a gate you approve.

| Phase | What happens | Deliverables | Depends on | Acceptance criteria (gate) | Effort |
| --- | --- | --- | --- | --- | --- |
| 0. Decisions & verification | Approve this plan; verify FEI format details; set the exam config | Approved decisions, exam config v1, rubric drafts | This blueprint | You sign off; every format fact has a source | 1 week |
| 1. Validation spikes | Test the risky assumptions before building screens | AI writing-score test on 30 human-marked texts; speech pipeline test on 20 recordings; TTS listening sample; 3 clickable screen mockups | Phase 0 | AI within ±2/20 of human on ≥ 75% of samples; transcription usable; you like the look | 2–3 weeks |
| 2. Content foundation | Competency map, item templates, first item bank | Competency list A2–C1; 150 listening + 150 reading items reviewed; writing/speaking prompts; diagnostic form | Phases 0–1 | Teacher review passed; one correct answer per item; level tags agreed | 3–5 weeks, overlaps Phase 3 |
| 3. Core build | Accounts, item player, exam-mode runner, scoring, learner model, planner, error notebook | Working app on your phone: diagnostic → plan → daily mission → feedback | Phase 1 decisions | You complete a full diagnostic and 7 days of missions without blocking bugs | 4–6 weeks |
| 4. Trials, simulator, progress, map | Weekly trial, full simulation, reports, dashboard, journey map, tutor overlay | MVP feature set | Phase 3 + enough content | A full simulation runs with exact timings; estimates show ranges and disclaimers | 3–4 weeks |
| 5. Use & calibrate | You study with it daily; we fix and tune | Bug fixes, tuned planner, expanded item bank to \~300 + 300 | Phase 4 | 4 weeks of daily use; weekly retention of the habit; estimates stable week to week | 4+ weeks, ongoing |
| 6. Version 2 | Live speaking, calibration model, richer story, public release prep | v2 features | Phase 5 data | Decided at the Phase 5 gate | Later |

**Testing in every phase:** unit tests on scoring, planner and mastery maths; a fixed set of “golden” writing and speaking samples re-scored after every AI prompt change; exam-mode timing tests; accessibility checks on each screen.

## 10. Risks and mitigations

The two risks that can sink the product are misleading scores and thin content; both are addressed before most screens are built (Phase 1 and 2).

| Risk | Type | Impact | Mitigation |
| --- | --- | --- | --- |
| AI feedback is wrong or inconsistent | Educational | Learns errors; loses trust | Rubric-bound prompts; double scoring with disagreement check; golden-sample regression tests; “report this correction” button; teacher spot checks |
| Speaking/writing scores don't match the real exam | Educational | False confidence before exam day | Calibrate on human-marked samples and your official result; always show ranges; never call it a score, call it an estimate |
| Misleading readiness predictions | Product / ethical | You book the exam too early | Readiness requires the target on two full simulations in a row; ranges and disclaimers everywhere; show the weakest skill first |
| Poor French audio | Educational | Listening practice feels fake | Best-quality TTS plus human-recorded items for exam-style content; varied accents (France, Canada, Africa); native review |
| Item bank too small | Content | Memorised questions, inflated scores | Templates + AI drafting + teacher review; track exposure; retire overused items; never reuse boss/simulation items in practice |
| TCF format or IRCC table changes | External | Wrong prep | Versioned exam config and score table; quarterly check of FEI and IRCC pages |
| Copyright of official materials | Legal | Takedown | Only original items, modelled on public format descriptions; no copied official questions |
| Privacy of recordings and data | Legal / trust | Data leak | Private storage, encryption, auto-delete recordings after 90 days by default, export and delete in settings; check that speech/AI vendors don't train on data |
| AI operating costs | Financial | Bill grows with use | Route cheap tasks to small models; cache explanations; cap daily AI usage per user; pre-generate audio |
| Motivation drops after 2–3 weeks | Product | App unused | 15-minute floor mission, rest-day-friendly streaks, visible skill gains, weekly report that feels like a coach |
| Scope creep | Delivery | MVP never ships | Phase gates; this document's MVP list is the contract |
| Speech recognition misreads accented French | Technical | Unfair speaking feedback | Show transcript so you can see misheard words; score content from transcript but pronunciation only as practice feedback |

**Multimedia risks added on 2026-10-16:** illustration style drifting between artists (one illustrator per art direction, a written style guide); media production becoming the bottleneck (measure hours on the prototype before committing to chapters); large videos on slow connections (adaptive streaming, low-data mode, offline downloads); animation slowing older phones (motion budget per screen, reduced-motion setting, test on a mid-range Android); unclear licences or voice consent (contract and consent record for every voice, no copied media).

## Update 2026-10-16: multimedia, story and beginner-friendly plan

Your additional requirements are now part of the plan. Sections 12–18 cover them, and section 11 now holds one merged decision list. Nothing earlier was removed. Three earlier choices changed slightly:

- **Story depth:** upgraded from “light map” to “illustrated, narrated chapters with characters”, but built one chapter at a time.
- **Video:** added to the plan, used for short scenes, not for long courses.
- **First build:** a single polished mission (section 16) comes before the full MVP in section 8, to test the experience before investing in content.

**Glossary for this document.** *Frontend*: the part you see and touch. *Backend*: the computer in the cloud that stores your progress and talks to AI services. *Library*: ready-made code that other people wrote and we reuse. *API*: a service we call over the internet, usually paid per use. *Claude agent skill*: a set of written instructions that helps Claude (the AI building the app) work better; it never goes inside the app itself.

## 12. Interactive learning experience

Every mission mixes at least three modes: you hear French, you respond (tap, speak or write), and something in the world reacts. The exam simulator stays plain and strict; all of the interactivity lives in training.

### Audio and speaking

| Feature | How it works in TCF QUEST | Training mode | Exam mode |
| --- | --- | --- | --- |
| French voices | Pre-recorded human audio for exam-style items; high-quality synthetic voices for story lines and drills | Replay, slow down to 0.75×, transcript after answering | One play only, no speed control, no transcript |
| Dialogues, interviews, announcements | Scripted to match TCF listening task types (station announcement, radio interview, phone message, debate) | Pause and tap a word for its meaning | As in the real test |
| Recording | Hold-to-talk or tap-to-start, waveform shown, playback of your own answer | Re-record allowed | One recording, timer visible |
| Transcription | Speech-to-text turns your answer into text so you can see what was understood | Shown with misheard words highlighted | Hidden until the report |
| AI spoken feedback | Rubric scores, corrected sentences, better phrasings, one thing to fix next time | Immediately | Only in the final report |
| Role-play | A character asks questions (speaking T1/T2/T3 style) and reacts to what you say | Version 1: turn-by-turn (you record, it replies). Version 2: live conversation | Examiner role-play only, neutral tone |

### Video

- **Short scenes (30–90 seconds):** a café order, a landlord call, a job interview, a town meeting. Each is followed by 2–4 questions and a vocabulary card set.
- **Interactive pauses:** the video stops at a decision point (“What does Claire mean?”) and continues after you answer.
- **Subtitles:** off by default; French subtitles and a transcript available in training after a first viewing.
- **Mobile delivery:** videos streamed in several qualities that adapt to your connection (called adaptive streaming), with a low-data option and download-for-offline for the current week's missions.
- **Not in exam mode:** the real TCF listening section is audio-based (with images on screen for some items), so the simulator uses audio, not video.

### Getting legal, affordable media

The cheapest safe path is to own everything we use: write our own scripts, then produce the media ourselves or commission it. Content from TV, YouTube, podcasts or official TCF material cannot be copied into the app, even for practice.

| Media | Option | Cost (rough) | Quality | Recommended use |
| --- | --- | --- | --- | --- |
| Narration and drills | Synthetic French voices (TTS) | Cents per minute | Good, slightly flat in emotion | Story narration, vocabulary, tutor speech |
| Exam-style listening | Freelance French voice actors from France, Québec, Belgium, West Africa recording our scripts | Roughly US$50–150 per finished minute, varies widely | Natural, authentic accents | Diagnostic, bosses, simulations |
| Middle ground | Record a few speakers once, then use voice tools only with their written consent | Medium | Good | Later, if volume grows |
| Video scenes | Illustrated or lightly animated scenes with real voice audio | Moderate, mostly illustration time | Fits the art direction | Version 1 video |
| Live-action video | Small shoots with actors | High | Most realistic | Only later, a few flagship scenes |
| AI-generated video | Text-to-video tools | Low to moderate | Uncanny lips and faces; licensing terms vary | Avoid for people speaking; maybe for backgrounds |
| Open licences | Creative Commons images and sounds (check each licence for commercial use) | Free | Mixed | Backgrounds and sound effects only |

**Quality control for every media file:** a native speaker checks the script before recording, a second listen checks audio clarity and level, every file carries its source, licence and consent record in the content library, and AI voices are labelled as synthetic in the credits.

## 13. Storytelling and art direction

I recommend direction A, “Carnet d'expédition”: an illustrated travel-journal world with editorial typography. It looks premium and adult, it is achievable with a small illustration budget, and its calm style keeps the French text readable.

### How the story works

- **World.** You are an explorer charting five regions of a French-speaking world. Each region is a chapter, with its own place, light and palette (a market town, a river city, a university quarter, a parliament of debates, a high observatory).
- **Characters.** A small recurring cast, each tied to a skill: a guide who narrates and explains grammar (the tutor's face), a radio host (listening), a journalist (reading and writing), a debater (speaking T3), and an examiner who appears only at bosses.
- **Narrated introductions.** Each mission opens with 20–40 seconds of narration over an illustrated scene, written at your current level so it is listening practice.
- **Dialogue choices.** You choose what to say, in French. Choices are graded for meaning and register (“tu” vs “vous”, politeness), and the character reacts with a line and an expression.
- **Character reactions.** Short illustrated poses (pleased, confused, impressed) and a reply that recasts your mistake correctly, the way a good teacher does.
- **Unlockable locations.** A place opens on the map when its competencies are mastered, never by points.
- **Transitions and achievements.** A 1–2 second page-turn or map pan between scenes; achievement moments are a full-screen illustrated card with a single line, and you can skip them.
- **Weekly boss.** The weekly mini-trial is framed as a story event (“the town council asks for your opinion”), but the questions themselves are plain exam style.
- **Separation rule.** Exam mode leaves the story entirely: a neutral, quiet interface, with only a short story beat before and after.

### Three art directions

|  | A. Carnet d'expédition (recommended) | B. Cinéma nocturne | C. Affiche moderne |
| --- | --- | --- | --- |
| Feel | Illustrated explorer's journal: watercolour-and-ink environments, paper textures, handwritten annotations as accents | Dark, filmic interface with painted night scenes, warm light sources, slow parallax | Bold flat shapes inspired by French travel posters, strong colour blocks, geometric type |
| Typography | Editorial serif for titles, clean sans-serif for reading, a restrained script only for map labels | High-contrast serif titles, light sans body on dark | Geometric sans titles, neutral sans body |
| Colour and light | Warm paper base, one accent colour per region, soft daylight | Deep blue-black base, amber highlights | Two to three saturated colours per chapter |
| Motion | Ink-drawn reveals, map pan, gentle drifting clouds | Slow camera moves, light flicker | Snappy shape transitions |
| Strengths | Mature, calm, clearly “expedition”, easy to read for long study sessions | Most cinematic and dramatic | Cheapest to illustrate, very clean |
| Weaknesses | Needs a consistent illustrator | Dark themes tire the eyes over long reading; harder to make accessible | Can feel like a marketing site; less immersive |
| Illustration cost | Medium | High | Low |
| Beginner-friendliness to build | High | Medium | High |

**Avoided in all directions:** generic dashboard cards, rainbow gradients, glassy effects everywhere, random sparkles, mascots that look childish, and animations that delay a learner who just wants to study.

**Design system to set before any screen is built:** colour tokens (base, text, accent per region, success, error), two typefaces with defined sizes, spacing scale, one panel style, an icon set, motion rules (durations, when motion is allowed), and a light and dark mode. A 1-page mood board per direction can be made in Phase 0 so you choose by looking, not by reading.

## 14. Skills and technologies

Of the six resources, two are Claude agent skills (help for the AI building the app) and four are app building blocks. Use Reanimated and the Expo audio approach now, Lottie for a few celebration moments, the two skill collections as design and code guidance, and keep Rive for later. Checked on GitHub on 2026-10-16; I could not read release dates, so versions must be re-checked when development starts.

### The six resources you listed

| Resource | Kind | What it does, in plain words | Advantages | Disadvantages | Beginner-friendly? | Needed in v1? | Cost / licence | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) | Claude agent skill | Instructions that push Claude toward distinctive, non-generic interface design: a clear concept, deliberate type pairing, restrained motion, accessibility | Directly targets the “generic AI dashboard” look you want to avoid | Written for websites; mobile-specific parts must be adapted | Yes, you never touch it; Claude reads it | Yes, during design-system work | Free; licence in the repo's LICENSE.txt (not checked) | **Use now**, for design guidance |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | Claude agent skills (8) | Rule sets for Claude: React performance, UI review, React Native guidelines, writing, deploying to Vercel | `react-native-guidelines` and `web-design-guidelines` fit our build; MIT licence | Several skills are for Vercel and Next.js websites, which we won't use | Yes | Partly | Free, MIT | **Use** the React Native and UI-review skills; **skip** the Vercel deploy ones |
| [React Native Reanimated](https://github.com/software-mansion/react-native-reanimated) | App library | Smooth animations that run without stuttering: panel slides, map pans, button feedback | Industry standard, actively maintained, included in Expo | Version 4 needs React Native's “New Architecture” (Expo's default now) | Medium; Claude writes it, simple uses are easy | Yes | Free, MIT | **Use now** |
| [Lottie React Native](https://github.com/lottie-react-native/lottie-react-native) | App library | Plays small vector animations made by designers (a stamp landing, a compass spinning) | Huge free and paid animation catalogue; works on web too; Apache-2.0 | Animations are fixed movies, not interactive; version 6 needs a recent React Native | Yes | A few uses | Free library; animation files free to paid | **Use lightly** for completion and achievement moments |
| [Rive React Native 2.0 (Nitro)](https://github.com/rive-app/rive-nitro-react-native) | App library + design tool | Interactive animations that react to the learner, e.g. a character whose expression changes with your answer | Best option for living characters and an animated map; MIT | New rewrite; needs Expo SDK 53+ and a custom app build rather than the simple Expo Go preview app (inferred); you must learn the Rive editor or hire a Rive animator | Low | No | Library free; Rive editor has free and paid plans (check) | **Later** (v2), once characters are designed |
| [Expo audio recording example](https://github.com/expo/audio-recording-example) | Example app | Shows how to record, save, and play back audio on phones with Expo | Made by the Expo team; exactly our recording need | No licence shown, so we read it but don't copy its code | Yes, as a reference | As reference | Free | **Reference only**; we use Expo's own audio package |

### Other technology decisions

Each row follows your seven questions. The “Default” column is my recommendation.

| Need | What it does | Why we need it | Options | Default | Pros / cons of default | Beginner-friendly? | v1? | Cost (verify before use) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Audio playback & recording | Plays French audio, records your voice | Listening and speaking are half the exam | expo-audio; older expo-av | **expo-audio** | Official, maintained / limited advanced audio editing | Yes | Yes | Free |
| Video playback | Plays scenes with pause points and subtitles | Interactive scenes | expo-video; web video player | **expo-video** | Official, supports streaming / no interactive features built in (we add them) | Yes | Yes | Free |
| Video hosting | Stores videos and streams the right quality for your connection | Smooth video on mobile data | Mux; Cloudflare Stream; Bunny Stream; plain file storage | **Plain storage for the prototype; Bunny or Cloudflare Stream at launch** | Cheap and simple / streaming services add a monthly bill | Yes | Later | Low, per minute stored and watched |
| French text-to-speech | Turns written French into spoken audio | Narration, drills, tutor voice | Azure neural voices; ElevenLabs; Google Cloud TTS | **Azure** for breadth of French accents; **ElevenLabs** to test for story narration | Many French (France and Canada) voices / some sound flat | Yes (simple API) | Yes | Cents per minute of audio |
| French speech-to-text | Writes down what you said | Speaking feedback | Azure Speech; OpenAI transcription; Deepgram | **Azure Speech**, compared in Phase 1 with one alternative | French and Canadian French supported; also offers pronunciation assessment (French support to confirm) / account setup is fiddly | Medium | Yes | Cents per minute |
| AI feedback & tutor | Scores and corrects speaking and writing, plays characters | The core teaching value | Claude; OpenAI; Gemini | **Claude** | Strong French and careful explanations / per-use cost | Yes | Yes | Per use; capped per day |
| Live voice conversation | Talk with a character in real time | Realistic role-play | Realtime voice APIs | **Not in v1** | Impressive / costly, complex, harder to grade | No | No | Higher per minute |
| Backend & storage | Keeps your account, progress and recordings | Progress across devices | Supabase; Firebase | **Supabase** | One service for database, login, files / one more account to manage | Medium | Yes (small) | Free tier to start |

## 15. Platform: web app or Expo mobile app

Recommendation: **Option B, Expo (React Native)**. Microphone recording, offline audio, notifications and later store release all work more reliably in a real app, and Expo still lets you test instantly: you scan a QR code and the app opens on your own phone through the free Expo Go app, and the same code can also open in a browser.

| Requirement | A. Web app / PWA | B. Expo mobile app |
| --- | --- | --- |
| What it is | A website that behaves like an app and can be added to your home screen | A real iPhone/Android app written once in JavaScript |
| Microphone | Works in modern browsers, but iPhone Safari has more limits and asks permission more often | Reliable, standard permission prompt |
| Audio and video | Good; background audio and offline caching are weaker on iPhone | Good, including offline downloads |
| Storytelling and animation | Excellent on desktop; heavy animation can stutter on older phones | Smooth with Reanimated, Lottie, later Rive |
| Notifications | Possible but limited on iPhone (only after adding to home screen) | Standard push notifications |
| Testing | Open a link; easiest of all | Scan a QR code with Expo Go; nearly as easy. Some advanced libraries later need a custom build |
| Cost | Cheapest hosting | Free to build; Apple developer account about US$99/year and Google about US$25 once, only when publishing |
| Maintenance | One web codebase | One codebase for iPhone, Android and web; yearly Expo upgrades |
| Store distribution | Not in stores (or wrapped later with extra work) | Built for App Store and Google Play |
| Beginner-friendly | Very | Good, with Claude doing the coding |

**Why not start with the web and switch later?** Switching means rebuilding the interface, and the riskiest parts of this product (recording, playing exam audio once, a smooth story feel on a phone) are exactly where the web is weakest. Testing them on a real phone from day one avoids a nasty surprise. **What the web option is still good for:** a quick clickable mock-up of screens in Phase 0, which doesn't need to be the real app.

## 16. First prototype: « Le Marché de Belleville »

One 10–12 minute mission, built to the final quality bar, answers the three questions that decide the whole product: does the experience feel premium, does real speaking feedback work in French, and do you want to come back tomorrow? Target level B1, speaking-focused, set in chapter 2 (La Vie Quotidienne).

### The mission, step by step

1. **Story introduction (40 s).** An illustrated market street fades in with ambient sound. The narrator: « Vous arrivez au marché. Madame Roux, la fromagère, a besoin d'aide… » French subtitles can be toggled.
2. **Audio conversation (60–90 s).** A recorded dialogue between Madame Roux and a customer about a missing delivery, in natural spoken French. Training controls: replay once, slow speed.
3. **Comprehension challenge.** Four questions in TCF style plus one interactive step: drag the delivery details onto a note card. Wrong answers show the exact sentence in the transcript.
4. **Voice recording.** Madame Roux asks you to leave a phone message for the supplier (60 seconds, like a speaking T2 situation). You record, listen back, and may re-record once.
5. **Feedback.** Your transcript appears, then rubric feedback: task completed?, clarity, vocabulary, grammar, with 2 corrected sentences and 1 improved model answer. Clearly labelled “AI feedback, practice estimate”.
6. **Animated completion.** Madame Roux reacts, the market location stamps onto your journal map, and a short Lottie animation plays (skippable).
7. **Progress update.** Your speaking estimate, two competencies (« conditionnel de politesse », « exprimer un problème ») and the error notebook update, and tomorrow's mission preview appears.

### Real vs sample

| Part | Prototype approach | Why |
| --- | --- | --- |
| Illustrations, narration, dialogue audio | Real, final quality, but just this one scene | We are testing how it feels |
| Comprehension questions | Real content, stored in the app (no database yet) | No need for a content system for one mission |
| Recording and playback | Real, on your phone | Biggest technical risk |
| Transcription | Real speech-to-text service | Biggest quality risk |
| AI feedback | Real Claude call through a small secure backend function | API keys must never sit inside the app |
| Fallback | A clearly labelled “sample feedback” if the AI call fails | Demo never breaks |
| Progress, error notebook | Saved on the phone only | A cloud account isn't needed for one user and one mission |
| Accounts, planner, map with many chapters | Not built; shown as static placeholders | Saves weeks |

### What it validates and how we judge it

- **Experience:** you complete it 3 times on different days and rate it at least 8/10 for “feels premium” and “I'd do this daily”.
- **Speaking pipeline:** the transcript is accurate enough on 20 test recordings (yours and others), and AI feedback matches a French teacher's judgement on most of them.
- **Performance:** opens in under 3 seconds on a mid-range Android phone; animations stay smooth.
- **Cost:** AI and speech cost per mission measured (target: a few cents).
- **Production effort:** we record how many hours the illustration, audio and writing took, which tells us what a full chapter will cost.

Rough effort: 3–5 weeks part-time, plus illustration and voice-actor time. This replaces the “clickable mock-up” part of Phase 1 in section 9.

## 17. Build order, and what to avoid

First the prototype mission, second the learning core, then the rest of the MVP; story richness and live conversation come after the core proves itself.

| Order | What | Why now |
| --- | --- | --- |
| 1st | Planning documents + art direction choice + exam-fact verification | Cheap decisions before expensive work |
| 2nd | Prototype mission (section 16) | Tests feel, speaking pipeline, cost and production effort |
| 3rd | Learning core: accounts, content library, diagnostic, planner, error notebook, writing feedback | What actually raises your NCLC |
| 4th | Exam simulator, weekly trial, progress reports | Measurement you can trust |
| 5th | Chapter 2–4 story content, journal map, video scenes | Grows on a proven core |
| Later | Rive characters, live voice role-play, store release, other learners, payments | Expensive or only needed at scale |

**What to avoid as a first-time app creator**

- **Building everything at once.** Finish one mission end to end before starting the next feature.
- **Too many services.** Each new account (analytics, streaming, payments) is another bill, password and failure point. Add one only when a feature needs it.
- **Putting secret keys inside the app.** Anyone can extract them; AI and speech calls always go through the backend.
- **Live voice AI and custom 3D or game engines early.** Impressive, but they multiply cost and bugs.
- **AI-generated content without review.** Wrong French taught confidently is the worst outcome for a learning app.
- **Copying media from the internet.** Use only what we own or what has a clear commercial licence.
- **Skipping version control.** All work goes into a GitHub repository from day one, so any mistake can be undone.
- **Chasing perfect design before testing on a real phone.** Test on your own device every week.
- **Unlimited AI usage.** Set a daily cap and a monthly budget alert on every paid service.

**Added costs from the multimedia plan (rough, verify before buying):** illustration for one chapter roughly US$500–2,500 depending on the artist; voice actors roughly US$50–150 per finished minute; TTS and speech recognition a few dollars a month for one learner; video streaming under US$10/month at personal scale; Apple and Google developer accounts only when publishing.

## 18. Project organisation

Ten short planning documents, each with one owner question, live in this project while we plan; when development starts they move into a `docs` folder in the code repository so the code and the decisions stay together. This blueprint is the source for all of them.

| # | Document | Answers | Built from | When |
| --- | --- | --- | --- | --- |
| 1 | Product requirements (PRD) | What are we building and for whom? | Sections 1, 2, 8 | Phase 0 |
| 2 | Design system & visual identity | How does everything look and move? | Section 13 + chosen art direction | Phase 0 |
| 3 | Screen-by-screen specification | What is on each screen and what happens? | Section 5 | Phase 0–1 |
| 4 | Learning & assessment specification | How do levels, plans, scoring and unlocks work? | Sections 0, 6 | Phase 0–1 |
| 5 | Multimedia content strategy | How do we produce and check audio, video, art? | Section 12 | Phase 0 |
| 6 | Technology decision record | Which tool, why, and what we rejected | Sections 7, 14, 15 | Phase 0, updated as we go |
| 7 | Feature backlog (prioritised) | What is next, in order? | Sections 8, 17 | Phase 0, then weekly |
| 8 | Milestone roadmap | Which phase, what gate, when? | Sections 9, 16 | Phase 0 |
| 9 | QA checklist | How do we know a feature is done? | Sections 9, 16 | Phase 1 |
| 10 | Unresolved decisions | What still needs your call? | Section 11 | Always current |

**Keeping approved choices consistent.** Every decision gets one line in a decision log: what was decided, the date, why, and what it replaced. A decision changes only when you approve the change, and the log keeps the old one. I also save approved decisions to project memory so every future conversation starts from them.

| Date | Decision | Status |
| --- | --- | --- |
| 2026-10-16 | Planning phase; no code until you approve development | Approved |
| 2026-10-16 | Exam simulation stays strictly separate from gamified training | Approved (your requirement) |
| 2026-10-16 | Unlocks based on mastery, never points | Approved (your requirement) |
| 2026-10-16 | Decisions 1–12 in section 11 | Awaiting your approval |

## 11. Decisions for your approval

Twelve decisions block the next step, merged from the first plan (1–7) and your multimedia requirements (8–12). Each has a recommended default; you can approve them all at once. Everything else (exact colours, XP numbers, notification times) can be decided during the build.

| # | Decision | Options | Recommended default | Why |
| --- | --- | --- | --- | --- |
| 1 | Who is v1 for? | Just you / public from day one | **Just you first**, built so others can join later | Halves scope; your use is the best validation |
| 2 | Exam target for the plan | NCLC 7 / NCLC 9 / NCLC 10 | **NCLC 7 as floor, NCLC 9 as plan target**; C1/C2 as a later personal goal | NCLC 7 is eligibility; higher levels earn points; C2 adds no Express Entry points |
| 3 | Platform | Expo app / web app (PWA) / native | **Expo** (section 15) | Reliable microphone, audio and notifications; still testable instantly on your phone |
| 4 | Backend & AI services | Supabase + Claude + Azure Speech / alternatives | **Supabase + Claude + Azure Speech**, confirmed by the prototype | Simple, cheap, swappable |
| 5 | Navigation | Your 5 tabs / 4 tabs + tutor everywhere | **4 tabs + tutor button** | Tutor works best in context |
| 6 | Question content | AI-only / AI + teacher review / buy content | **AI drafts + paid teacher review** (20–40 hours) | Quality without huge cost |
| 7 | Story depth | Light map / illustrated narrated chapters | **Illustrated, narrated chapters with characters, built one chapter at a time** (changed from “light map”) | Matches your new requirements without building all chapters up front |
| 8 | Art direction | A Carnet d'expédition / B Cinéma nocturne / C Affiche moderne | **A, Carnet d'expédition**, confirmed with mood boards | Premium and adult, readable, medium cost |
| 9 | First thing to build | Full MVP / one polished prototype mission | **Prototype mission « Le Marché de Belleville »** (section 16) | Tests feel, speaking feedback and cost before content investment |
| 10 | Media sourcing | All synthetic / all human / mixed | **Mixed:** human voice actors for exam-style audio, synthetic voices for narration and drills, illustrated video scenes, no AI-generated talking faces | Authentic where the exam needs it, cheap elsewhere |
| 11 | Animation tools | Reanimated / Lottie / Rive | **Reanimated + a few Lottie moments now, Rive later** | Simple first; interactive characters once designed |
| 12 | Prototype budget cap | Your call | **Suggest US$500–1,000** for illustration, voice actors and services | Enough for one high-quality mission; protects you from surprise costs |

**Also need from you, not decisions:** your exam date if booked, your daily study minutes, and whether you can get 30–50 writing/speaking samples marked by a teacher (or should we budget for it).

**Next step after your approval:** Phase 0 (planning documents, mood boards, exam-fact checks), then the prototype mission in section 16. No app code until you say go.
