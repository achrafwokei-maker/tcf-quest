# Free online beta: audit and plan (2026-10-19)

Status: B0–B1 approved and done (local code only). B2 (accounts, deployment) awaits approval.

Goal: 5–20 friends use TCF Quest from a permanent HTTPS link, on phone or computer, with the Mac off. Budget US$0. Nothing below has been deployed or built yet.

## 1. Already compatible with free hosting

- Frontend: static Vite build (752 KB). Any static host can serve it.
- Content: 512 KB of JSON, read-only. It ships with the app.
- Backend: plain Python 3.12 + FastAPI. No Mac-only code in the rules engine (scoring, answer keys, planner, exams, journey, vocab).
- Exam timers are stored as timestamps in the database (`exam.py`), so a server restart or sleep does not reset a running exam.
- Migrations are numbered and run in order (`db.migrate`), so the schema upgrades safely on each database.
- Per-tester isolation is cheap: the app is single-learner per database file (`profile id = 1`), so one database per tester needs no schema change.
- AI failures already show "failed, try again" states instead of crashing.

## 2. Depends on the Mac today

| Part | Why it can't go online as is |
| --- | --- |
| Ollama + Qwen3 8B (writing feedback, speaking feedback, examiner) | Needs ~6 GB RAM and a GPU. No free host runs it. |
| TTS worker (Pocket TTS, Piper) | Too heavy for free hosts. |
| Speech to text (MLX Whisper) | MLX runs only on Apple Silicon. |
| `data/tcfquest.db` (one SQLite file) | Free hosts wipe their disk on restart. |
| No login | Fine locally; online, anyone with the link could use or overwrite data. |

## 3. Cheapest real $0 architecture (recommended)

```
Phone / laptop ──HTTPS──> Render free web service (one service)
                            ├─ serves the built web app (same origin, no CORS)
                            ├─ FastAPI backend, unchanged rules engine
                            ├─ data: one Turso database per tester (SQLite-compatible, free)
                            └─ AI: Cloudflare Workers AI REST API (free plan)
                                 • LLM feedback / examiner (Llama 3.1 8B fast or Qwen3 30B-A3B)
                                 • Whisper large-v3-turbo speech to text
                                 • MeloTTS French for live examiner replies (browser voice as fallback)
Listening audio: pre-rendered on the Mac with the natural voices, shipped as static files (zero quota).
Development: unchanged on the Mac (Ollama, local worker, local SQLite), chosen by env settings.
```

Why this: it keeps the existing FastAPI backend instead of a rewrite. Cloudflare-only hosting would mean rewriting the backend in JavaScript, which breaks your "don't rebuild" rule.

Verified facts and sources:
- [Render free](https://render.com/docs/free): sleeps after 15 min idle, about 1 min to wake (a loading page shows meanwhile). 750 free hours/month. Disk is wiped on restart. Rollback to the 2 previous deploys. The page doesn't say a card is needed to deploy. Going over the bandwidth limit with no card on file suspends the service; it does not bill. **Check at signup: if Render asks for a card, stop and tell me.**
- [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/): 10,000 neurons/day free. On the free plan, requests fail when the quota runs out; they are not billed.
- [MeloTTS model page](https://developers.cloudflare.com/workers-ai/models/melotts/): `lang: "fr"` is documented, MP3 output. Quality is untested; we'll listen before relying on it.
- [Turso pricing](https://turso.tech/pricing.md): free plan has 100 databases, 5 GB, 500M rows read and 10M written per month, and no overage billing. [Python SDK](https://docs.turso.tech/sdk/python/reference): described as sqlite3-compatible.

**Main technical risk:** the code uses `sqlite3.Row` and `conn.backup`, and the Turso docs don't confirm either. Step 1 of the plan is a 1-hour test that answers this. If they're missing, a small row adapter goes in `db.py` (contained change).

Rejected options:
- [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces-overview): Docker apps need a paid plan.
- [Koyeb](https://www.koyeb.com/docs/faqs/pricing): needs a card.
- Render Postgres: expires after 30 days, and we'd have to rewrite the SQL.
- Groq free tier: limits are only from [third-party pages](https://eesel.ai/blog/groq-pricing). Keep it as a possible later speech-to-text backup, not in v1.

## 4. Free-tier limits for 5–20 testers (honest)

Rough AI cost per action, from the official price table:

| Action | Neurons (approx.) |
| --- | --- |
| Writing feedback (about 2,500 tokens in, 800 out) | 35–40 |
| One speaking task with examiner (4.5 min speech to text, about 10 short examiner turns, about 2 min of voice) | 350–400 |
| Repeat-after-me check (about 10 s of speech) | about 8 |

The shared 10,000/day budget buys roughly:
- **about 25 full speaking tasks per day**, or
- **about 250 writing feedbacks per day**, or a mix of the two.

With 20 testers, that is about one speaking task each per day plus some writing. That is enough for a beta. It is not enough for "unlimited AI".

Guards we'll build:
- **Per-tester daily cap** (default 450 neurons, about 1 speaking task + 2 writing feedbacks).
- **Global stop at 9,000/day.**
- **Clear message when the cap is reached:** "AI feedback resting until tomorrow; everything else works".

Other limits:
- **Waking up:** the first visit after 15 min idle waits about 1 minute.
- **AI feedback isn't the same as locally:** online feedback comes from a different model than Qwen3 8B. It stays labelled "unofficial estimate", and rules still decide every score.
- **No pronunciation scoring:** same as today.

## 5. Development vs stable beta

| | Development | Beta |
| --- | --- | --- |
| Where | Your Mac | Render |
| Git branch | `phase-1-foundation` | new `beta` branch (deploys from GitHub) |
| AI | Ollama + local voices | Workers AI |
| Data | `data/tcfquest.db` | Turso, one database per tester |
| Settings | `.env` absent, defaults to local | Render environment variables (secrets never in git) |

Unfinished work only ever lives on `phase-1-foundation`.

## 6. Automatic deployment of approved changes

1. I build and test on `phase-1-foundation` (`scripts/test.sh` must pass).
2. You say "approve for beta".
3. I merge into `beta` and push.
4. A GitHub Actions check (free for public repos) runs the tests. Render deploys only when they pass.
5. If something breaks, roll back in Render to the previous deploy (one click), or I revert the merge on `beta`.

The public repo stays the open-source copy. `beta` is a branch of it, so no private data goes online.

## 7. How tester progress survives updates

- Data lives in Turso, never on Render's disk, so deploys and restarts can't erase it.
- Each tester's database is migrated on first request after a deploy, using the same numbered migrations.
- **Beta rule: migrations only add (new tables or columns), never drop or rename.**
- Backups:
  - Before each deploy, a script copies every tester database into a dated file on your Mac (`data/beta-backups/`, git-ignored).
  - Turso's own restore point is a second safety net.
- Running exams survive restarts because their timers are stored timestamps. Deploys happen when you choose, so we avoid deploying while a friend is mid-mock.

## 8. What needs changing, easiest first

1. Build-time setting: the web app's audio and API paths work unchanged (same origin). No change needed.
2. Env-based config for AI and voice URLs (already partly `TCFQUEST_DB`). Small.
3. FastAPI serves the built `web/dist`. Small.
4. Invite codes: one private code per tester, saved in a secure cookie, mapping to that tester's database. Codes are stored hashed in Render's secrets. Small–medium.
5. Request-scoped database (`db_path()` per tester) plus per-tester migration on first use. Medium.
6. Turso connection in `db.py`, plus a row adapter if needed. Medium (the risk named in section 3).
7. AI provider switch: `ai.py` chooses Ollama (dev) or Workers AI (beta) for LLM, speech to text and live TTS. Includes daily caps and quota-exhausted messages. Medium.
8. Pre-render listening audio to static files and serve them before calling live TTS. Medium (one-time Mac job, size to check).
9. Mobile pass: test at phone width and test the microphone over HTTPS on iPhone Safari and Android Chrome. Medium.
10. CI workflow (tests on `beta`) and the backup script. Small.

## 9. Smallest safe implementation plan

- **B0 (no accounts needed):** Turso compatibility test using the local libSQL file mode. Pre-render audio and check its size. Write the AI provider switch with a fake provider in tests.
- **B1 (code only, all local):** steps 2–5 and 7 above, tested locally with 2 fake testers. Exam-restart test.
- **B2 (needs you):** you create free Cloudflare, Turso and Render accounts (no card) and paste the API tokens into Render's settings yourself. I never see or commit them. Then the first deploy to a private, unlisted URL. Only you test it.
- **B3:** mobile and microphone checks on your phone. Invite 2–3 friends, watch quotas for a week, then open it to up to 20.

Approval needed before B2 (accounts, public URL) and before inviting anyone.
