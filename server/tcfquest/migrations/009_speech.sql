-- 009: learner recordings and their local transcriptions (milestone M5). Audio files stay in data/recordings.

CREATE TABLE speech_recording (
  id           INTEGER PRIMARY KEY,
  path         TEXT NOT NULL,                          -- relative to data/
  context      TEXT NOT NULL DEFAULT 'check',          -- check | eo-task | mission (what it was recorded for)
  context_ref  TEXT,                                   -- e.g. a task or item id
  duration_s   REAL NOT NULL DEFAULT 0,
  transcript   TEXT NOT NULL DEFAULT '',
  confidence   REAL NOT NULL DEFAULT 0,               -- 0..1, recogniser confidence, NOT a pronunciation score
  status       TEXT NOT NULL,                          -- ok | uncertain | no_speech | too_short | too_quiet | engine_off
  typed_text   TEXT,                                   -- learner's own correction or typed fallback
  engine       TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
