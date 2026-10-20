# Decision log

One line per decision: what, when, why, what it replaced. A decision changes only with the learner's approval; old entries stay.

| Date | Decision | Why | Replaces | Status |
| --- | --- | --- | --- | --- |
| 2026-10-16 | Planning first; no code until approved | Avoid building the wrong thing | — | Superseded (dev approved) |
| 2026-10-16 | Exam mode strictly separate from gamified training | Faithful exam practice | — | Approved |
| 2026-10-16 | Unlocks by mastery, never points | Map must reflect real ability | — | Approved |
| 2026-10-16 | v1 is for the learner only, built so others can join later | Halves scope | — | Approved |
| 2026-10-16 | Targets: NCLC 7 floor, NCLC 9 plan target; C1/C2 personal goal tracked separately | Express Entry rules | — | Approved |
| 2026-10-16 | Art direction A, "Carnet d'expédition" | Premium, adult, readable | — | Superseded the same day |
| 2026-10-16 | Story: illustrated chapters, built one at a time | Grow on a proven core | Light map | Approved |
| 2026-10-16 | First mission: « Le Marché de Belleville » | Tests feel and speaking pipeline | Full MVP first | Approved |
| 2026-10-16 | **Budget US$0**: no paid APIs, subscriptions or cloud | The learner's constraint | US$500–1,000 + US$50/mo | Approved |
| 2026-10-16 | **Local web app** on the Mac, opened in a browser | Free local AI needs the Mac anyway; mic works in browsers on localhost | Expo mobile app | Approved |
| 2026-10-16 | **Local AI stack**: Ollama + Qwen3 8B; local Whisper STT; local French TTS | US$0 and private | Claude API + Azure Speech | Approved |
| 2026-10-16 | Backend Python 3.12 + FastAPI; SQLite with numbered SQL migrations | Speech tools are Python; one local file DB | Supabase | Approved |
| 2026-10-16 | Five destinations including a Tutor tab | The learner's prompt | 4 tabs + tutor button | Approved |
| 2026-10-16 | All voices locally generated for now | US$0 | Human voice actors for exam audio | Approved (revisit if audio feels fake) |
| 2026-10-16 | Learning content in version-controlled JSON (`content/`), learner data in SQLite | Answer keys reviewable like code | — | Chosen by Claude |
| 2026-10-16 | Project-local tools (`.tools/`, uv) instead of Homebrew/system changes | No system-wide changes | — | Chosen by Claude |
| 2026-10-16 | Fonts self-hosted via Fontsource (OFL): Fraunces + Source Sans 3 | No network calls; free licence | — | Chosen by Claude |
| 2026-10-16 | Git commits under a no-reply email | Keeps personal email out of a future public repo | — | Chosen by Claude |
| 2026-10-16 | **Game-style art direction** from 6 references: 3D designer-doll avatars, Paris-night palette, game-store layout, France level map, glossy avatar creator | The learner wants the app to feel like a fun game | Carnet d'expédition | Approved |
| 2026-10-16 | Avatar built at onboarding (questions + self-description); basic skin first; new skins earned per French level (mastery-based) | Motivation tied to real progress | — | Approved |
| 2026-10-16 | Images made with ChatGPT / Nano Banana during development only; each image approved by the learner first | Quality art at no extra cost; the learner keeps control | CSS/SVG-only art | Approved |
| 2026-10-16 | No text inside generated images; all labels drawn in code | AI images garble text; French must be exact | — | Chosen by Claude |
| 2026-10-16 | **Experience blueprint approved** (docs/EXPERIENCE_BLUEPRINT.md), with the learner's notes integrated as Part II | Experience before code | Form onboarding, dashboard Home | Approved |
| 2026-10-16 | XB1 One companion guide + story characters + neutral examiner; companion says *tu*, service characters *vous*. Companion name: **Céleste** (cartographer) | Coherent, alive, teaches register; name fits chapter V's observatory | Camille (planning name in the notes) | Approved |
| 2026-10-16 | XB2 Avatar optional and after the first challenge; mic and reminders asked only when needed | Value before data | Mandatory avatar step | Approved |
| 2026-10-16 | XB2b "Which TCF section concerns you most?" returns as an informational question (never treated as a measurement) | The learner's notes | Question dropped | Approved |
| 2026-10-16 | XB3 Diagnostic in four short parts (6–8 min) spread over week 1 | Less intimidating | One 60–75 min block | Approved |
| 2026-10-16 | XB4 Weekly rhythm (5 of 7 days) instead of a daily streak; reviews capped at 10/day | No guilt, no backlog | Daily streak | Approved |
| 2026-10-16 | XB5 One story, several level versions | Everyone gets the story at a winnable level | One version per mission | Approved |
| 2026-10-16 | XB6 No pronunciation scoring in v1; content feedback only | No validated French pronunciation tool yet | — | Approved |
| 2026-10-16 | XB7 Companion lines from templates, AI only for conversations and corrections | Short, accurate, fast | Free AI chat | Approved |
| 2026-10-16 | XB8 Reminders: in-app + browser notifications only | Local app limits | — | Approved |
| 2026-10-16 | XB9 MVP scope (section K) and milestone order (section M), as revised in Part II | Smallest complete journey | — | Approved |
| 2026-10-16 | **TCF Canada identity:** every mission, lesson and tool is tagged with the exam section/task it serves; nothing generic | The learner's non-negotiable | — | Approved |

| 2026-10-16 | **Voices:** Pocket TTS (Estelle) + Piper (Tom, Siwis) in a separate local worker; text normalised before speech; browser voice only as fallback | Free, local, natural; objective test in VOICE_EVALUATION.md; final call = the learner's ratings | Paid cloud TTS (not allowed) | Pending ratings |
| 2026-10-17 | Gap-audit decisions: (1) foundations first (M1–M3) before speaking/writing; (2) Claude writes original items during development, marked draft/reviewed, with a reserved assessment pool; (3) P2 frozen (Belleville playable; avatar, map, new story chapters on hold); (4) EE/EO AI scores = unofficial estimates, calibrated later with teacher samples if available | Smallest path to a complete adaptive loop | — | Approved |
| 2026-10-17 | Weakness key = an item's primary competency; retests only use unseen, reviewed training items (secondary-competency items allowed) | Confirms transfer, not memorisation | Re-showing the failed item | Approved (M1) |
| 2026-10-17 | Skill estimates: weighted MAP Rasch-style ability, item difficulty = CEFR band, slope 2.2, weak self-rating prior, range = θ ± 1 SE; speaking/writing confidence capped "low" while evidence is proxy-only | Deterministic, transparent, narrows with evidence | Plain accuracy averages (ignore item level) | Approved (M2) |
| 2026-10-17 | Writing: word = characters between spaces (FEI's exact rule unpublished); single-task exam split 15/20/25 min (suggested, labelled); AI rubric `ee-rubric-v2` (5 criteria 0–5, error vs style, double scoring, quote check, deterministic elision and a/à rules); only errors become weaknesses; AI evidence weight 0.2 (0.1 on disagreement), writing confidence ≤ medium after 3 agreeing tasks | Rules decide, AI explains; bounded, auditable feedback | Single AI pass; AI-invented categories | Approved (M4) |
| 2026-10-17 | Speaking: examiner = Qwen3 limited to 1–2 short lines, T2 facts hidden from the learner + mandatory surprise; feedback `eo-rubric-v2` content/language only (no pronunciation score); turns with confidence < 0.75 (unless typed/corrected) excluded from corrections and weaknesses; evidence 0.2, halved on disagreement or mostly uncertain transcripts | Recognition errors must never become learner penalties | Pronunciation scoring (no validated free tool) | Approved (M6) |
| 2026-10-17 | Exam engine: forward-only items, one audio play (question after audio), section countdowns server-side, each exam taken once, exam evidence weight 0.6, wrong exam answers → weaknesses but not the review notebook (reserved items stay out of reviews); weekly trial due every 7 days | Realistic conditions; unseen items confirm transfer | Allowing back-navigation (TCF computer test rules unverified: stricter choice taken) | Approved (M7) |
| 2026-10-17 | **Public on GitHub**: code MIT, content CC BY-NC-SA 4.0; personal details removed and published with a fresh history; models never committed (downloaded by setup scripts) | The owner wants others to use it; Piper (GPL) runs as a separate process and isn't distributed | — | Approved |
| 2026-10-17 | Vocabulary cards are a self-graded memory aid kept apart from skill evidence (no effect on estimates or weak points); 15 reviews + 8 new a day | Self-grading is not proof of ability; light daily load | Counting card grades as evidence | Approved |

## Open

- Exam date, daily minutes (onboarding asks), teacher-marked samples.
- Usage terms of ChatGPT and Google Flow images for an open-source repository (check before publishing).
- How avatars are produced for other learners later (pre-made library vs local image generation).

## Dependency licences (checked 2026-10-16)

| Package | Licence |
| --- | --- |
| React, React Router, Vite, Vitest, Tailwind CSS, Motion | MIT |
| TypeScript | Apache-2.0 |
| lucide-react | ISC |
| Fraunces, Source Sans 3 (Fontsource) | SIL OFL 1.1 |
| FastAPI, uvicorn, httpx | MIT / BSD-3-Clause / BSD-3-Clause |
| Ollama | MIT |
| Qwen3 8B | Apache-2.0 |
| Pocket TTS 3.3.0 (code / French model) | MIT / CC-BY 4.0. Voices: Estelle Kyutai; VCTK voices (George, Paul, Charles) CC-BY 4.0; Jean (EARS) CC-BY-NC 4.0, personal use only |
| Piper 1.8.0 | GPL-3.0 (engine, in a separate process). Voices: Siwis CC-BY 4.0, Tom AGPL-3.0, UPMC CC-BY-SA 4.0, Gilles CC0 |
| MLX Whisper (evaluation only) | MIT |
| libsql 0.1.11 (online beta only, optional extra) | MIT |
| PyJWT 2.15 + cryptography 50 (online beta only) | MIT / Apache-2.0 or BSD-3-Clause |
| Firebase JS SDK 12.19.0 (loaded only online) | Apache-2.0 |


## 2026-10-19: online beta foundations (B0–B1, local only)

- **Hosting plan** in `docs/ONLINE_BETA_PLAN.md` (Render free + Turso + Cloudflare Workers AI). Approved for local code only; accounts and deployment still need the owner's approval.
- **Database driver:** `TCFQUEST_DB_BACKEND=libsql` runs the same code on libSQL (Turso). libsql has no `row_factory`, `backup` or named parameters, so a thin adapter in `db.py` provides them. The whole backend suite runs on both drivers in `scripts/test.sh`.
- **One database per tester**, chosen by a signed invite cookie (`testers.py`). Codes are stored only as SHA-256 hashes in an environment variable. Wrong codes are rate-limited. Local mode is unchanged.
- **AI provider switch** (`ai.py`): Ollama locally, Workers AI online. There is a per-tester daily neuron cap (default 450), and on top of that the Cloudflare free plan fails rather than bills. Quota errors become the usual "failed, try again" state, with a clear message.
- **Content audio pre-recorded** with the natural voices (170 lines, 5.8 MB MP3, `content/audio/tts/`) so the beta needs no cloud TTS for content. Only lines not pre-recorded use MeloTTS or the browser voice. Attribution is in that folder's README. Jean (CC-BY-NC) is never used for these files.
- **Not yet verified (needs accounts, B2):** the Workers AI JSON-schema mode with our prompts, MeloTTS French quality, libsql embedded replicas against a real Turso database, and whether Render asks for a card.

## 2026-10-20: owner-only login for the beta

- The owner is the only tester for now, so the main login is a password: `TCFQUEST_OWNER = name:scrypt$salt$hash`, made by `scripts/beta_admin.py owner NAME`. The password is asked hidden and only the hash leaves the Mac.
- The name picks the database, so changing the password (re-run with the same name) keeps all progress.
- The invite-code path (`TCFQUEST_INVITES`) stays optional for later testers; unset, it does nothing.
- Every `/api` route, including AI, needs the signed login cookie. Wrong passwords are rate-limited (10 per 15 min).

## 2026-10-20: learner accounts (Firebase Authentication, built locally, not deployed)

- **Firebase Auth, Spark plan:** Google sign-in plus email/password. No payment method is needed. Verified limits ([pricing](https://firebase.google.com/pricing), [limits](https://firebase.google.com/docs/auth/limits)):
  - up to 50k monthly active users;
  - 1,000 verification emails and 150 password-reset emails per day.
- **How sign-in works:** the browser signs in with Firebase. The server checks the ID token (RS256, Google's public certificates, audience, issuer, expiry), then sets the existing signed cookie, so all other routes are unchanged. Email/password accounts need a verified email.
- **Databases:** one Turso database per account, created on first sign-in. The Turso free plan allows 100 databases, so `TCFQUEST_MAX_ACCOUNTS` defaults to 50. `TCFQUEST_ACCOUNT_MAP=email:achraf` keeps the owner's existing database. `TCFQUEST_BLOCKED` revokes an account.
- **Export:** `/api/account/export` ("Download my data" in Settings) returns every table as JSON. The owner's `beta_admin.py backup` copies whole databases.
- **Not free or not done:**
  - Cloud AI stays limited to the shared Cloudflare 10k neurons/day plus per-account caps. There is no global cap across accounts yet; Cloudflare's free plan stops at the quota instead of billing.
  - The Firebase web config is public by design; protection comes from the server-side token check.
