"""TCF Quest local API. Run with: uvicorn tcfquest.main:app --host 127.0.0.1 --port 8787"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator, Literal

from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from . import (accounts, ai, avatar, content, db, estimates, feedback, notebook, onboarding, planner, reviews, sessions, tts,
               exam, journey, speaking, speaking_ai, speech, testers, vocab, weakness, writing, writing_ai)

SKILLS = ("listening", "reading", "speaking", "writing")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if testers.beta_mode():  # each tester's database is prepared on their first request
        yield
        return
    conn = db.connect()
    db.migrate(conn)
    with db.transaction(conn):
        weakness.backfill(conn)          # once, from past attempts
        estimates.update(conn)           # skill estimates always reflect the stored evidence
    conn.close()
    yield


app = FastAPI(title="TCF Quest", version="0.1.0", lifespan=lifespan)
app.add_middleware(testers.TesterMiddleware)


def get_db() -> Iterator[sqlite3.Connection]:
    """One short-lived connection per request (SQLite connections are per-thread)."""
    conn = db.connect()
    try:
        testers.ensure_ready(conn)
        yield conn
    finally:
        conn.close()


# ---------- online beta: invite code login (inactive locally) ----------

class InviteIn(BaseModel):
    code: str = Field(min_length=4, max_length=100)


@app.get("/api/beta/me")
def beta_me(request: Request):
    if not testers.beta_mode():
        return {"beta": False, "tester": None, "firebase": None}
    return {"beta": True, "tester": testers.verify(request.cookies.get(testers.COOKIE)),
            "firebase": accounts.public_config()}


class FirebaseIn(BaseModel):
    id_token: str = Field(min_length=20, max_length=5000)


@app.post("/api/auth/firebase")
def auth_firebase(body: FirebaseIn, response: Response):
    """Google or email/password sign-in done in the browser by Firebase; checked here."""
    if not accounts.enabled():
        raise HTTPException(404, "Not available")
    name, email = accounts.sign_in(body.id_token)
    response.set_cookie(testers.COOKIE, testers.sign(name), max_age=testers.COOKIE_MAX_AGE,
                        httponly=True, secure=True, samesite="lax")
    return {"beta": True, "tester": name, "email": email}


@app.get("/api/account/export")
def account_export(conn: sqlite3.Connection = Depends(get_db)):
    """Download everything stored for this learner (JSON)."""
    return Response(json.dumps(accounts.export(conn), ensure_ascii=False, default=str), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="tcfquest-{date.today()}.json"'})


@app.post("/api/beta/login")
def beta_login(body: InviteIn, request: Request, response: Response):
    if not testers.beta_mode():
        raise HTTPException(404, "Not available")
    client = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "?")
    name = testers.login(body.code, client)
    response.set_cookie(testers.COOKIE, testers.sign(name), max_age=testers.COOKIE_MAX_AGE,
                        httponly=True, secure=True, samesite="lax")
    return {"beta": True, "tester": name}


@app.post("/api/beta/logout")
def beta_logout(response: Response):
    response.delete_cookie(testers.COOKIE)
    return {"ok": True}


# ---------- health ----------

@app.get("/api/ai/budget")
def ai_budget(conn: sqlite3.Connection = Depends(get_db)):
    """Today's free cloud AI allowance for this learner (beta only; locally unlimited)."""
    return ai.budget()


@app.get("/api/health")
async def health():
    # Online, before sign-in there is no learner database: report that the server is up, nothing more.
    if testers.beta_mode() and not db.current_tester.get():
        return {"ok": True, "schema_version": None, "ai": {"running": ai.provider() == "workers"}}
    conn = db.connect()
    try:
        testers.ensure_ready(conn)
        schema = db.schema_version(conn)
    finally:
        conn.close()
    return {"ok": True, "schema_version": schema, "ai": await ai.status()}


# ---------- profile ----------

Skill = Literal["listening", "reading", "speaking", "writing"]


class ProfileIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=40)
    goal: Literal["tcf_canada", "general"] = "tcf_canada"
    target_cefr: Literal["B2", "C1", "C2"] = "B2"
    target_nclc: int = Field(default=9, ge=4, le=10)
    exam_date: date | None = None
    daily_minutes: int = Field(default=30, ge=10, le=120)
    hardest_skills: list[Skill] = Field(default_factory=list, max_length=4)
    ui_language: Literal["en", "fr"] = "en"


def _profile_row(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        return None
    out = dict(row)
    out["hardest_skills"] = json.loads(out["hardest_skills"])
    return out


@app.get("/api/profile")
def get_profile(conn: sqlite3.Connection = Depends(get_db)):
    return {"profile": _profile_row(conn)}


@app.put("/api/profile")
def put_profile(body: ProfileIn, conn: sqlite3.Connection = Depends(get_db)):
    values = body.model_dump()
    values["exam_date"] = body.exam_date.isoformat() if body.exam_date else None
    values["hardest_skills"] = json.dumps(sorted(set(body.hardest_skills)))
    with db.transaction(conn):
        conn.execute(
            """
            INSERT INTO profile (id, display_name, goal, target_cefr, target_nclc, exam_date,
                                 daily_minutes, hardest_skills, ui_language, onboarded_at)
            VALUES (1, :display_name, :goal, :target_cefr, :target_nclc, :exam_date,
                    :daily_minutes, :hardest_skills, :ui_language, datetime('now'))
            ON CONFLICT (id) DO UPDATE SET
              display_name = excluded.display_name, goal = excluded.goal,
              target_cefr = excluded.target_cefr, target_nclc = excluded.target_nclc,
              exam_date = excluded.exam_date, daily_minutes = excluded.daily_minutes,
              hardest_skills = excluded.hardest_skills, ui_language = excluded.ui_language
            """,
            values,
        )
        for skill in SKILLS:
            conn.execute("INSERT OR IGNORE INTO skill_profile (skill) VALUES (?)", (skill,))
    return {"profile": _profile_row(conn)}


# ---------- dashboard summary ----------

def _streak(conn: sqlite3.Connection, today: date) -> int:
    days = {r[0] for r in conn.execute("SELECT day FROM study_day")}
    streak, cursor = 0, today
    if cursor.isoformat() not in days:  # today not studied yet: streak still counts from yesterday
        cursor -= timedelta(days=1)
    while cursor.isoformat() in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


@app.get("/api/summary")
def summary(conn: sqlite3.Connection = Depends(get_db)):
    profile = _profile_row(conn)
    if profile is None:
        raise HTTPException(404, "No profile yet")
    today = date.today()
    xp = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM xp_event").fetchone()[0]
    skills = [dict(r) for r in conn.execute("SELECT * FROM skill_profile ORDER BY skill")]
    open_mistakes = conn.execute(
        "SELECT COUNT(*) FROM mistake WHERE status != 'mastered'"
    ).fetchone()[0]
    due_reviews = conn.execute(
        "SELECT COUNT(*) FROM mistake WHERE status != 'mastered' AND next_review <= ?",
        (today.isoformat(),),
    ).fetchone()[0]
    minutes_today = conn.execute(
        "SELECT COALESCE(minutes, 0) FROM study_day WHERE day = ?", (today.isoformat(),)
    ).fetchone()
    return {
        "profile": profile,
        "xp": xp,
        "streak": _streak(conn, today),
        "minutes_today": minutes_today[0] if minutes_today else 0,
        "skills": skills,
        "open_mistakes": open_mistakes,
        "due_reviews": due_reviews,
        "diagnostic_done": any(s["evidence"] > 0 for s in skills),
        "history": [dict(r) for r in conn.execute(
            "SELECT skill, cefr_low, cefr_high, confidence, source, created_at FROM progress_history "
            "ORDER BY id DESC LIMIT 20")],
        "weaknesses": {"active": conn.execute("SELECT COUNT(*) FROM weakness WHERE state != 'mastered'").fetchone()[0],
                       "mastered": conn.execute("SELECT COUNT(*) FROM weakness WHERE state = 'mastered'").fetchone()[0]},
    }


# ---------- avatar ----------

class AvatarIn(BaseModel):
    gender: Literal["woman", "man", "nonbinary", "unspecified"]
    hair: Literal["short", "medium", "long", "curly", "braids", "bald"]
    hair_colour: Literal["black", "brown", "auburn", "blond", "grey", "dyed"]
    skin_tone: int = Field(ge=1, le=6)
    facial_hair: Literal["none", "stubble", "beard", "moustache"] = "none"
    glasses: bool = False
    vibe: Literal["street", "classic", "sporty", "artsy"]
    description: str = Field(default="", max_length=600)


class SkinIn(BaseModel):
    skin: str


def _avatar_payload(conn: sqlite3.Connection) -> dict:
    row = conn.execute("SELECT * FROM avatar WHERE id = 1").fetchone()
    data = dict(row) if row else None
    if data:
        data["glasses"] = bool(data["glasses"])
    return {"avatar": data, "skins": avatar.skins_for(conn), "reached_level": avatar.reached_level(conn)}


@app.get("/api/avatar")
def get_avatar(conn: sqlite3.Connection = Depends(get_db)):
    return _avatar_payload(conn)


@app.put("/api/avatar")
def put_avatar(body: AvatarIn, conn: sqlite3.Connection = Depends(get_db)):
    values = body.model_dump()
    values["glasses"] = int(body.glasses)
    values["description"] = body.description.strip()
    with db.transaction(conn):
        conn.execute(
            """
            INSERT INTO avatar (id, gender, hair, hair_colour, skin_tone, facial_hair, glasses, vibe, description)
            VALUES (1, :gender, :hair, :hair_colour, :skin_tone, :facial_hair, :glasses, :vibe, :description)
            ON CONFLICT (id) DO UPDATE SET
              gender = excluded.gender, hair = excluded.hair, hair_colour = excluded.hair_colour,
              skin_tone = excluded.skin_tone, facial_hair = excluded.facial_hair, glasses = excluded.glasses,
              vibe = excluded.vibe, description = excluded.description, updated_at = datetime('now')
            """,
            values,
        )
    return _avatar_payload(conn)


@app.put("/api/avatar/skin")
def equip_skin(body: SkinIn, conn: sqlite3.Connection = Depends(get_db)):
    if body.skin not in avatar.SKIN_IDS:
        raise HTTPException(404, "Unknown skin")
    if conn.execute("SELECT 1 FROM avatar WHERE id = 1").fetchone() is None:
        raise HTTPException(409, "Create your avatar first")
    if not avatar.is_unlocked(conn, body.skin):
        raise HTTPException(403, "This skin unlocks at a higher French level")
    conn.execute("UPDATE avatar SET equipped_skin = ?, updated_at = datetime('now') WHERE id = 1", (body.skin,))
    return _avatar_payload(conn)


# ---------- exercise sets (milestone 1) ----------

class AnswerIn(BaseModel):
    item_id: str
    response: str | list[str] | None = None
    duration_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    hints_used: int = Field(default=0, ge=0, le=3)
    plays: int = Field(default=1, ge=0, le=20)
    audio_off: bool = False
    skipped: bool = False


def _set_or_404(set_id: str, conn: sqlite3.Connection | None = None) -> content.ExerciseSet:
    if set_id == reviews.REVIEW_ID:
        s = (reviews.get_or_start(conn) if conn is not None else None)
        if s is None:
            raise HTTPException(404, "Nothing to review right now")
        return s
    s = content.get_set(set_id)
    if s is None or s.context == "exam":          # reserved exam sets are only served by the exam engine
        raise HTTPException(404, "Unknown exercise set")
    return s


@app.get("/api/sets")
def list_sets():
    return {"sets": [
        {"id": s.id, "title": s.title, "level": s.level, "items": len(content.scored(content.playable(s))), "context": s.context,
         "group": s.group,
         "sections": sorted({i.tcf_target.section for i in s.items}), "tcf_target": s.tcf_target.model_dump()}
        for s in content.all_sets().values() if s.context != "exam"
    ]}


@app.get("/api/sets/{set_id}")
def get_set(set_id: str, conn: sqlite3.Connection = Depends(get_db)):
    s = _set_or_404(set_id, conn)
    state = sessions.load_state(conn, s)
    return {
        "set": {"id": s.id, "title": s.title, "level": s.level, "context": s.context,
                "tcf_target": s.tcf_target.model_dump(),
                "mission": s.mission.model_dump() if s.mission else None,
                "items": {i.id: content.public_item(i) for i in content.playable(s)}},
        "state": sessions.public_state(state, s),
    }


@app.post("/api/sets/{set_id}/answer")
def answer(set_id: str, body: AnswerIn, conn: sqlite3.Connection = Depends(get_db)):
    s = _set_or_404(set_id, conn)
    try:
        return sessions.submit(conn, s, body.item_id, body.response, duration_ms=body.duration_ms,
                               hints_used=body.hints_used, plays=body.plays, audio_off=body.audio_off,
                               skipped=body.skipped)
    except sessions.OutOfSync:
        state = sessions.load_state(conn, s)
        raise HTTPException(409, {"message": "This item was already answered.", "state": sessions.public_state(state, s)})


@app.post("/api/sets/{set_id}/hint")
def hint(set_id: str, item_id: str, conn: sqlite3.Connection = Depends(get_db)):
    s = _set_or_404(set_id, conn)
    item = content.item_by_id(s, item_id)
    if item is None:
        raise HTTPException(404, "Unknown item")
    if isinstance(item, content.TypeItem):
        return {"hint": item.hint or f"It starts with « {item.answers[0][0]} »."}
    if isinstance(item, content.ArrangeItem):
        return {"hint": item.hint or f"It starts with « {item.answers[0][0]} »."}
    return {"hint": getattr(item, "hint", None)}


@app.get("/api/sets/{set_id}/why/{item_id}")
def why(set_id: str, item_id: str, conn: sqlite3.Connection = Depends(get_db)):
    data = sessions.why(conn, _set_or_404(set_id, conn), item_id)
    if data is None:
        raise HTTPException(404, "Answer the item first")
    return data


@app.post("/api/sets/{set_id}/restart")
def restart(set_id: str, conn: sqlite3.Connection = Depends(get_db)):
    if set_id == reviews.REVIEW_ID:
        s = reviews.start(conn)
        if s is None:
            raise HTTPException(404, "Nothing to review right now")
        return {"state": sessions.public_state(sessions.load_state(conn, s), s)}
    s = _set_or_404(set_id)
    state = sessions.new_state(conn, s)
    return {"state": sessions.public_state(state, s)}


# ---------- today, notebook, reviews, mission report (milestone 4) ----------

@app.get("/api/today")
def today(minutes: int | None = None, conn: sqlite3.Connection = Depends(get_db)):
    """Today's plan (planner v1): ordered steps with a reason each, fitted to the minutes available."""
    if minutes is not None and not 5 <= minutes <= 180:
        raise HTTPException(422, "minutes must be between 5 and 180")
    p = planner.plan(conn, minutes)
    review = next((s for s in p["steps"] if s["kind"] == "review"), None)
    return {"plan": p, "mission": planner.best_mission(conn), "reviews_due": review["count"] if review else 0}


@app.get("/api/notebook")
def get_notebook(conn: sqlite3.Connection = Depends(get_db)):
    return {**notebook.listing(conn), "weaknesses": weakness.listing(conn)}


@app.post("/api/notebook/{mistake_id}/understood")
def understood(mistake_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if not notebook.mark_understood(conn, mistake_id):
        raise HTTPException(404, "Unknown or already mastered")
    return {**notebook.listing(conn), "weaknesses": weakness.listing(conn)}


@app.post("/api/reviews/start")
def start_reviews(conn: sqlite3.Connection = Depends(get_db)):
    s = reviews.start(conn)
    if s is None:
        raise HTTPException(404, "Nothing to review right now")
    return {"set_id": s.id, "items": len(s.items)}


@app.get("/api/sets/{set_id}/report")
def report(set_id: str, conn: sqlite3.Connection = Depends(get_db)):
    s = _set_or_404(set_id, conn)
    state = sessions.load_state(conn, s)
    since = state.get("started_at", "1970-01-01")
    ms = conn.execute("SELECT COALESCE(SUM(duration_ms), 0) FROM attempt WHERE context_id = ? AND created_at >= ?",
                      (s.id, since)).fetchone()[0]
    ids = [i.id for i in content.scored(content.playable(s))]
    reasons = [f"item:{i}" for i in ids] + [f"set:{s.id}"]
    xp = conn.execute(f"SELECT COALESCE(SUM(amount), 0) FROM xp_event WHERE created_at >= ? AND reason IN ({','.join('?' * len(reasons))})",
                      (since, *reasons)).fetchone()[0]
    originals = [feedback.original_id(i) for i in ids]
    mistakes = conn.execute(
        f"SELECT COUNT(*) FROM mistake WHERE status != 'mastered' AND last_seen >= ? AND item_id IN ({','.join('?' * len(originals))})",
        (since, *originals)).fetchone()[0]
    comps = sorted({c for i in content.scored(content.playable(s)) for c in i.competencies})
    rows = {r["competency"]: r for r in conn.execute(
        f"SELECT * FROM mastery WHERE competency IN ({','.join('?' * len(comps))})", comps)}
    return {
        "minutes": max(1, -(-ms // 60000)) if ms else 0,
        "xp": xp,
        "mistakes_in_notebook": mistakes,
        "summary": sessions.public_state(state, s)["summary"],
        "competencies": [{"id": c, "p_known": rows[c]["p_known"] if c in rows else 0.2,
                          "mastered": notebook.is_mastered(rows[c]) if c in rows else False} for c in comps],
    }


# ---------- onboarding and campaign (milestone 3) ----------

class OnboardingIn(BaseModel):
    step: str
    answers: dict = Field(default_factory=dict)


@app.get("/api/onboarding")
def get_onboarding(conn: sqlite3.Connection = Depends(get_db)):
    state = onboarding.load(conn)
    state["challenge_set"] = onboarding.challenge_set_for(state["answers"].get("self_rating"))
    return state


@app.put("/api/onboarding")
def put_onboarding(body: OnboardingIn, conn: sqlite3.Connection = Depends(get_db)):
    try:
        state = onboarding.save(conn, body.step, body.answers)
    except ValueError as e:  # pydantic ValidationError is a ValueError
        raise HTTPException(422, str(e).split("\n")[0])
    state["challenge_set"] = onboarding.challenge_set_for(state["answers"].get("self_rating"))
    return state


@app.post("/api/onboarding/restart")
def restart_onboarding(conn: sqlite3.Connection = Depends(get_db)):
    return onboarding.start_over_from_profile(conn)


@app.post("/api/onboarding/complete")
def complete_onboarding(conn: sqlite3.Connection = Depends(get_db)):
    try:
        return onboarding.complete(conn)
    except onboarding.Incomplete as e:
        raise HTTPException(409, f"Missing answers: {e}")


@app.get("/api/campaign")
def get_campaign(conn: sqlite3.Connection = Depends(get_db)):
    try:
        return onboarding.campaign(conn)
    except onboarding.Incomplete:
        raise HTTPException(404, "No profile yet")


# ---------- learner feedback and review queue (milestone 2) ----------

class FlagIn(BaseModel):
    kind: Literal["too_easy", "too_hard", "unclear", "dispute", "technical"]
    note: str = Field(default="", max_length=500)


class ResolveIn(BaseModel):
    note: str = Field(default="", max_length=500)


def _flag_call(fn, *args):
    try:
        out = fn(*args)
    except feedback.FlagError as e:
        raise HTTPException(e.status, str(e))
    estimates.update(args[0])            # disputes and technical flags change the evidence
    return out


@app.post("/api/attempts/{attempt_id}/flags")
def flag_attempt(attempt_id: int, body: FlagIn, conn: sqlite3.Connection = Depends(get_db)):
    return _flag_call(feedback.add_flag, conn, attempt_id, body.kind, body.note)


@app.get("/api/review")
def review(conn: sqlite3.Connection = Depends(get_db)):
    return feedback.review_queue(conn)


@app.post("/api/review/{flag_id}/accept")
def review_accept(flag_id: int, body: ResolveIn, conn: sqlite3.Connection = Depends(get_db)):
    return _flag_call(feedback.accept_dispute, conn, flag_id, body.note)


@app.post("/api/review/{flag_id}/reject")
def review_reject(flag_id: int, body: ResolveIn, conn: sqlite3.Connection = Depends(get_db)):
    return _flag_call(feedback.reject_dispute, conn, flag_id, body.note)


@app.post("/api/review/{flag_id}/close")
def review_close(flag_id: int, body: ResolveIn, conn: sqlite3.Connection = Depends(get_db)):
    return _flag_call(feedback.close_technical, conn, flag_id, body.note)


# ---------- backup ----------

@app.post("/api/backup")
def make_backup(conn: sqlite3.Connection = Depends(get_db)):
    if testers.beta_mode():
        raise HTTPException(403, "Online backups are made by the maintainer")
    return {"path": str(db.backup(conn))}


# ---------- voices (text-to-speech) ----------

class TtsIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    speaker: str | None = None          # a character name: picks that character's voice
    voice: str | None = None            # or an explicit voice id (Voice Studio previews)
    speed: float = Field(default=1.0, ge=0.75, le=1.25)


class VoiceSettingsIn(BaseModel):
    female: str | None = None
    male: str | None = None
    narrator: str | None = None
    speed: float | None = Field(default=None, ge=0.8, le=1.2)
    slow_speed: float | None = Field(default=None, ge=0.8, le=1.0)
    slow_mode: bool | None = None
    rating: tuple[str, int] | None = None     # (voice id, 1..5)


@app.get("/api/voices")
async def voices(conn: sqlite3.Connection = Depends(get_db)):
    worker = await tts.worker_voices()
    available = set()
    if worker:
        available |= {f"pocket:{v}" for v in worker.get("pocket", [])}
        available |= {f"piper:{v}" for v in worker.get("piper", [])}
    return {
        "worker_running": worker is not None,
        "voices": [{"id": vid, **{k: v[k] for k in ("label", "gender", "native", "licence", "cer", "speed", "engine")},
                    "available": vid in available} for vid, v in tts.VOICES.items()],
        "characters": tts.CHARACTERS,
        "settings": tts.get_settings(conn),
    }


@app.put("/api/voices/settings")
def put_voice_settings(body: VoiceSettingsIn, conn: sqlite3.Connection = Depends(get_db)):
    changes = body.model_dump(exclude_none=True, exclude={"rating"})
    for slot in ("female", "male", "narrator"):
        if slot in changes and changes[slot] not in tts.VOICES:
            raise HTTPException(422, f"Unknown voice {changes[slot]}")
    if body.rating:
        vid, stars = body.rating
        if vid not in tts.VOICES or not 1 <= stars <= 5:
            raise HTTPException(422, "Rating must be a known voice and 1–5")
        changes["ratings"] = {**tts.get_settings(conn)["ratings"], vid: stars}
    return tts.save_settings(conn, changes)


@app.post("/api/tts/text")
def tts_text(body: TtsIn):
    """The spoken version of a text (what the browser-voice fallback reads)."""
    return {"spoken": tts.spoken_text(body.text), "sentences": tts.sentences(body.text)}


@app.post("/api/tts")
async def tts_audio(body: TtsIn, conn: sqlite3.Connection = Depends(get_db)):
    voice_id = tts.voice_for(conn, body.speaker, body.voice)
    try:
        wav, native = await tts.synthesize(voice_id, body.text, body.speed)
    except Exception:
        if ai.provider() == "workers":  # not pre-recorded: cloud French voice, else the browser's
            try:
                mp3 = await run_in_threadpool(ai.speak, tts.spoken_text(body.text))
                return Response(mp3, media_type="audio/mpeg", headers={"X-Voice": "cloud", "X-Speed-Applied": "0"})
            except Exception:
                pass
        raise HTTPException(503, "The local voice engine is not running. Using the browser voice instead.")
    return Response(wav, media_type="audio/mpeg" if wav[:4] != b"RIFF" else "audio/wav", headers={
        "X-Voice": voice_id, "X-Speed-Applied": "1" if native else "0", "Cache-Control": "max-age=86400"})


# ---------- writing studio (EE T1–T3) ----------

class WritingStartIn(BaseModel):
    mode: Literal["training", "exam"] = "training"


class WritingTextIn(BaseModel):
    text: str = Field(max_length=6000)


def _score_in_background(sid: int) -> None:
    conn = db.connect()
    try:
        writing_ai.run(conn, sid)
    finally:
        conn.close()


@app.get("/api/writing")
def writing_tasks(conn: sqlite3.Connection = Depends(get_db)):
    return writing.listing(conn)


@app.get("/api/writing/tasks/{task_id}")
def writing_task(task_id: str, conn: sqlite3.Connection = Depends(get_db)):
    t = writing.get_task(task_id)
    if t is None or t.pool != "training":
        raise HTTPException(404, "Unknown writing task")
    return {"task": writing.public_task(t), "template": writing.task_file().templates[t.task].model_dump(),
            "history": writing.history(conn, task_id)}


@app.post("/api/writing/tasks/{task_id}/start")
def writing_start(task_id: str, body: WritingStartIn, conn: sqlite3.Connection = Depends(get_db)):
    try:
        return writing.start(conn, task_id, body.mode)
    except KeyError:
        raise HTTPException(404, "Unknown writing task")


def _writing_call(fn, *args):
    try:
        return fn(*args)
    except KeyError:
        raise HTTPException(404, "Unknown submission")
    except writing.Locked as e:
        raise HTTPException(409, str(e))


@app.get("/api/writing/submissions/{sid}")
def writing_get(sid: int, conn: sqlite3.Connection = Depends(get_db)):
    s = writing.submission(conn, sid)
    if s is None:
        raise HTTPException(404, "Unknown submission")
    return s


@app.put("/api/writing/submissions/{sid}")
def writing_save(sid: int, body: WritingTextIn, conn: sqlite3.Connection = Depends(get_db)):
    return _writing_call(writing.save, conn, sid, body.text)


@app.post("/api/writing/submissions/{sid}/submit")
def writing_submit(sid: int, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    s = _writing_call(writing.submit, conn, sid)
    if s["feedback_status"] == "pending":
        background.add_task(_score_in_background, sid)
    return s


@app.post("/api/writing/submissions/{sid}/feedback")
def writing_feedback_retry(sid: int, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    s = writing.submission(conn, sid)
    if s is None or s["status"] != "submitted":
        raise HTTPException(404, "Unknown submitted text")
    if s["feedback_status"] in ("failed", "none") and s["word_count"] > 0:
        conn.execute("UPDATE writing_submission SET feedback_status = 'pending' WHERE id = ?", (sid,))
        background.add_task(_score_in_background, sid)
    return writing.submission(conn, sid)


# ---------- speaking pipeline (local recording + transcription) ----------

class SpeechCorrectIn(BaseModel):
    text: str = Field(max_length=2000)


class CompareIn(BaseModel):
    target: str = Field(max_length=500)
    heard: str = Field(max_length=2000)


@app.post("/api/speech/transcribe")
async def speech_transcribe(request: Request, context: Literal["check", "eo-task", "mission"] = "check",
                            ref: str | None = None, conn: sqlite3.Connection = Depends(get_db)):
    """Body: a 16-bit PCM WAV recorded in the browser. Saved in data/recordings, never sent elsewhere."""
    data = await request.body()
    try:
        return await speech.transcribe(conn, data, context, ref)
    except speech.BadAudio as e:
        raise HTTPException(422, str(e))


@app.put("/api/speech/recordings/{rid}")
def speech_correct(rid: int, body: SpeechCorrectIn, conn: sqlite3.Connection = Depends(get_db)):
    if not speech.correct(conn, rid, body.text):
        raise HTTPException(404, "Unknown recording")
    return {"ok": True}


@app.delete("/api/speech/recordings/{rid}")
def speech_delete(rid: int, conn: sqlite3.Connection = Depends(get_db)):
    if not speech.delete(conn, rid):
        raise HTTPException(404, "Unknown recording")
    return {"ok": True}


@app.post("/api/speech/compare")
def speech_compare(body: CompareIn):
    return speech.compare(body.target, body.heard)


# ---------- speaking tasks EO T1–T3 (AI examiner) ----------

class EOStartIn(BaseModel):
    mode: Literal["training", "exam"] = "training"


class EOTurnIn(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    source: Literal["speech", "corrected", "typed"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    asr_status: str | None = None
    recording_id: int | None = None


def _eo_call(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except KeyError:
        raise HTTPException(404, "Unknown speaking task or session")
    except speaking.Ended as e:
        raise HTTPException(409, str(e))


def _eo_feedback_in_background(sid: int) -> None:
    conn = db.connect()
    try:
        speaking_ai.run(conn, sid)
    finally:
        conn.close()


@app.get("/api/eo")
def eo_tasks(conn: sqlite3.Connection = Depends(get_db)):
    return speaking.listing(conn)


@app.get("/api/eo/tasks/{task_id}")
def eo_task(task_id: str, conn: sqlite3.Connection = Depends(get_db)):
    t = speaking.get_task(task_id)
    if t is None or t.pool != "training":
        raise HTTPException(404, "Unknown speaking task")
    return {"task": speaking.public_task(t), "guide": speaking.task_file().guides[t.task].model_dump(),
            "history": speaking.history(conn, task_id)}


@app.post("/api/eo/tasks/{task_id}/start")
def eo_start(task_id: str, body: EOStartIn, conn: sqlite3.Connection = Depends(get_db)):
    return _eo_call(speaking.start, conn, task_id, body.mode)


@app.get("/api/eo/sessions/{sid}")
def eo_get(sid: int, conn: sqlite3.Connection = Depends(get_db)):
    return _eo_call(speaking.public, conn, sid)


@app.post("/api/eo/sessions/{sid}/begin")
def eo_begin(sid: int, conn: sqlite3.Connection = Depends(get_db)):
    return _eo_call(speaking.begin, conn, sid)


@app.post("/api/eo/sessions/{sid}/turn")
def eo_turn(sid: int, body: EOTurnIn, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    try:
        s = speaking.turn(conn, sid, body.text, body.source, body.confidence, body.asr_status, body.recording_id)
    except speaking.Ended as e:
        s = speaking.public(conn, sid)
        if s["feedback_status"] == "pending":
            background.add_task(_eo_feedback_in_background, sid)
        raise HTTPException(409, str(e))
    except KeyError:
        raise HTTPException(404, "Unknown session")
    if s["status"] == "ended" and s["feedback_status"] == "pending":
        background.add_task(_eo_feedback_in_background, sid)
    return s


@app.post("/api/eo/sessions/{sid}/end")
def eo_end(sid: int, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    s = _eo_call(speaking.end, conn, sid, "learner")
    if s["feedback_status"] == "pending":
        background.add_task(_eo_feedback_in_background, sid)
    return s


@app.post("/api/eo/sessions/{sid}/feedback")
def eo_feedback_retry(sid: int, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    s = _eo_call(speaking.public, conn, sid)
    if s["status"] == "ended" and s["feedback_status"] == "failed":
        background.add_task(_eo_feedback_in_background, sid)
    return s


# ---------- strict exam engine (weekly trials) ----------

class ExamAnswerIn(BaseModel):
    item_id: str
    response: str | None = None


class ExamPlayIn(BaseModel):
    item_id: str


def _schedule_exam_feedback(conn: sqlite3.Connection, aid: int, background: BackgroundTasks) -> None:
    """Writing/speaking sections closed by the engine (timeout, finish) still get their AI feedback."""
    row = conn.execute("SELECT sections FROM exam_attempt WHERE id = ?", (aid,)).fetchone()
    for sec in json.loads(row["sections"]) if row else []:
        for wid in sec.get("writing_submission_ids") or ([sec["writing_submission_id"]] if sec.get("writing_submission_id") else []):
            r = conn.execute("SELECT feedback_status, status FROM writing_submission WHERE id = ?", (wid,)).fetchone()
            if r and r["status"] == "submitted" and r["feedback_status"] == "pending":
                background.add_task(_score_in_background, wid)
        if sec.get("eo_session_id"):
            r = conn.execute("SELECT feedback_status, status FROM eo_session WHERE id = ?", (sec["eo_session_id"],)).fetchone()
            if r and r["status"] == "ended" and r["feedback_status"] == "pending":
                background.add_task(_eo_feedback_in_background, sec["eo_session_id"])


def _exam_call(fn, conn, aid, background, *args):
    try:
        out = fn(conn, aid, *args)
    except exam.ExamError as e:
        raise HTTPException(e.status, str(e))
    _schedule_exam_feedback(conn, aid, background)
    return out


@app.get("/api/exams")
def exams_list(conn: sqlite3.Connection = Depends(get_db)):
    return exam.listing(conn)


@app.post("/api/exams/{exam_id}/start")
def exams_start(exam_id: str, conn: sqlite3.Connection = Depends(get_db)):
    try:
        return exam.start(conn, exam_id)
    except exam.ExamError as e:
        raise HTTPException(e.status, str(e))


@app.get("/api/exams/attempts/{aid}")
def exams_get(aid: int, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    def get(c, a):
        exam._check_time(c, a)
        return exam.public(c, a)
    return _exam_call(get, conn, aid, background)


@app.post("/api/exams/attempts/{aid}/begin")
def exams_begin(aid: int, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    return _exam_call(exam.begin_section, conn, aid, background)


@app.post("/api/exams/attempts/{aid}/play")
def exams_play(aid: int, body: ExamPlayIn, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    return _exam_call(exam.play, conn, aid, background, body.item_id)


@app.post("/api/exams/attempts/{aid}/answer")
def exams_answer(aid: int, body: ExamAnswerIn, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    return _exam_call(exam.answer, conn, aid, background, body.item_id, body.response)


@app.post("/api/exams/attempts/{aid}/finish")
def exams_finish(aid: int, background: BackgroundTasks, conn: sqlite3.Connection = Depends(get_db)):
    return _exam_call(exam.finish_section, conn, aid, background)


# ---------- the adventure (one journey, presentation only) ----------

@app.get("/api/journey")
def journey_map(conn: sqlite3.Connection = Depends(get_db)):
    return journey.build(conn)


@app.get("/api/journey/continue")
def journey_continue(conn: sqlite3.Connection = Depends(get_db)):
    return journey.continue_step(conn)


# ---------- vocabulary cards (spaced repetition, retention aid only) ----------

class VocabGradeIn(BaseModel):
    grade: Literal["again", "hard", "good", "easy"]


@app.get("/api/vocab")
def vocab_overview(conn: sqlite3.Connection = Depends(get_db)):
    return vocab.overview(conn)


@app.get("/api/vocab/session")
def vocab_session(conn: sqlite3.Connection = Depends(get_db)):
    return {"cards": vocab.session(conn), **{k: v for k, v in vocab.overview(conn).items() if k in ("due", "new_today")}}


@app.post("/api/vocab/{card_id}/grade")
def vocab_grade(card_id: str, body: VocabGradeIn, conn: sqlite3.Connection = Depends(get_db)):
    try:
        return vocab.grade(conn, card_id, body.grade)
    except KeyError:
        raise HTTPException(404, "Unknown card")


# ---------- web app (online beta: one service serves the built frontend; locally Vite does) ----------

WEB_DIST = Path(os.environ.get("TCFQUEST_WEB_DIST", db.PROJECT_ROOT / "web" / "dist")).resolve()


@app.get("/{path:path}", include_in_schema=False)
def web_app(path: str):
    if os.environ.get("TCFQUEST_SERVE_WEB") != "1" or path.startswith("api/"):
        raise HTTPException(404, "Not found")
    dist = Path(os.environ.get("TCFQUEST_WEB_DIST", WEB_DIST)).resolve()
    f = (dist / path).resolve()
    if path and f.is_file() and dist in f.parents:
        # Hashed build files never change; the page itself must always be fresh after a deploy.
        return FileResponse(f, headers={"Cache-Control": "public, max-age=31536000, immutable"}
                            if f.parent.name == "assets" else None)
    return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})
