-- 010: speaking tasks EO T1–T3 with a local AI examiner (milestone M6).
-- 001 created an unused, always-empty placeholder `speaking_session`: replace it.
DROP TABLE IF EXISTS speaking_session;

CREATE TABLE eo_session (
  id               INTEGER PRIMARY KEY,
  task_id          TEXT NOT NULL,                      -- content/speaking task id
  task             TEXT NOT NULL,                      -- EO-T1 | EO-T2 | EO-T3
  mode             TEXT NOT NULL,                      -- training | exam
  status           TEXT NOT NULL,                      -- prep | active | ended
  turns            TEXT NOT NULL DEFAULT '[]',         -- [{role, text, source, confidence, asr_status, recording_id, at}]
  prep_s           INTEGER NOT NULL DEFAULT 0,
  talk_s           INTEGER NOT NULL,
  started_at       TEXT NOT NULL,
  talk_started_at  TEXT,
  ended_at         TEXT,
  end_reason       TEXT,                               -- time | learner
  ai_fallbacks     INTEGER NOT NULL DEFAULT 0,         -- examiner lines produced without the AI
  feedback         TEXT,
  feedback_status  TEXT NOT NULL DEFAULT 'none',       -- none | pending | done | failed
  feedback_model   TEXT,
  prompt_version   TEXT,
  agreement        TEXT
);
