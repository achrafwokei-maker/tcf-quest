-- 001: initial learner-state schema.
-- Learning content (chapters, lessons, questions, answer keys) lives in /content as
-- version-controlled JSON so it can be reviewed like code. The database stores only
-- what the learner does.

CREATE TABLE profile (
  id              INTEGER PRIMARY KEY CHECK (id = 1),   -- single local learner in v1
  display_name    TEXT NOT NULL,
  goal            TEXT NOT NULL DEFAULT 'tcf_canada',   -- tcf_canada | general
  target_cefr     TEXT NOT NULL DEFAULT 'B2',           -- B2 | C1 | C2 (personal goal)
  target_nclc     INTEGER NOT NULL DEFAULT 9,           -- exam goal, tracked separately
  exam_date       TEXT,                                 -- ISO date or NULL
  daily_minutes   INTEGER NOT NULL DEFAULT 30,
  hardest_skills  TEXT NOT NULL DEFAULT '[]',           -- JSON array of skill ids
  ui_language     TEXT NOT NULL DEFAULT 'en',           -- language for explanations
  onboarded_at    TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL                                   -- JSON
);

-- Current estimate per skill (listening, reading, speaking, writing).
CREATE TABLE skill_profile (
  skill        TEXT PRIMARY KEY,
  cefr_low     TEXT,
  cefr_high    TEXT,
  confidence   TEXT NOT NULL DEFAULT 'none',            -- none | low | medium | high
  evidence     INTEGER NOT NULL DEFAULT 0,              -- number of scored items behind it
  updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE progress_history (
  id         INTEGER PRIMARY KEY,
  skill      TEXT NOT NULL,
  cefr_low   TEXT,
  cefr_high  TEXT,
  confidence TEXT NOT NULL,
  source     TEXT NOT NULL,                             -- diagnostic | weekly | boss | simulation
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row per answered item (MCQ, writing, speaking turn...).
CREATE TABLE attempt (
  id           INTEGER PRIMARY KEY,
  item_id      TEXT NOT NULL,                           -- id in /content
  content_ver  TEXT NOT NULL,                           -- content version when answered
  skill        TEXT NOT NULL,
  competency   TEXT,
  mode         TEXT NOT NULL,                           -- training | exam
  context      TEXT NOT NULL,                           -- mission | diagnostic | weekly | boss | practice
  context_id   TEXT,
  response     TEXT NOT NULL,                           -- JSON
  correct      INTEGER,                                 -- 1/0 for keyed items, NULL for open tasks
  score        REAL,                                    -- 0..1 for open tasks when scored
  hints_used   INTEGER NOT NULL DEFAULT 0,
  duration_ms  INTEGER,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX attempt_skill_idx ON attempt (skill, created_at);
CREATE INDEX attempt_item_idx ON attempt (item_id);

-- Per-competency mastery (Bayesian knowledge tracing style).
CREATE TABLE mastery (
  competency   TEXT PRIMARY KEY,
  p_known      REAL NOT NULL DEFAULT 0.2,
  attempts     INTEGER NOT NULL DEFAULT 0,
  days_seen    TEXT NOT NULL DEFAULT '[]',              -- JSON array of ISO dates
  last_seen    TEXT,
  next_review  TEXT
);

CREATE TABLE mistake (
  id             INTEGER PRIMARY KEY,
  skill          TEXT NOT NULL,
  category       TEXT NOT NULL,                         -- e.g. grammar.conditionnel
  item_id        TEXT,
  context        TEXT NOT NULL,                         -- question or prompt shown
  learner_answer TEXT NOT NULL,
  correction     TEXT NOT NULL,
  explanation    TEXT NOT NULL,
  recurrence     INTEGER NOT NULL DEFAULT 1,
  status         TEXT NOT NULL DEFAULT 'open',          -- open | improving | mastered
  ease           REAL NOT NULL DEFAULT 2.5,             -- spaced repetition
  interval_days  INTEGER NOT NULL DEFAULT 0,
  next_review    TEXT NOT NULL DEFAULT (date('now')),
  first_seen     TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX mistake_review_idx ON mistake (status, next_review);

CREATE TABLE mission_progress (
  mission_id    TEXT PRIMARY KEY,
  status        TEXT NOT NULL DEFAULT 'available',      -- locked | available | in_progress | completed
  step          INTEGER NOT NULL DEFAULT 0,
  state         TEXT NOT NULL DEFAULT '{}',             -- JSON, resumable step state
  best_score    REAL,
  completed_at  TEXT,
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE unlock (
  key         TEXT PRIMARY KEY,                         -- chapter:2, boss:2, mission:x
  unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
  reason      TEXT NOT NULL                             -- the mastery rule that unlocked it
);

CREATE TABLE xp_event (
  id         INTEGER PRIMARY KEY,
  amount     INTEGER NOT NULL,
  reason     TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE study_day (
  day      TEXT PRIMARY KEY,                            -- ISO date; drives the streak
  minutes  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE achievement (
  id        TEXT PRIMARY KEY,
  earned_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE study_plan (
  id         INTEGER PRIMARY KEY,
  period     TEXT NOT NULL,                             -- day | week | month
  starts_on  TEXT NOT NULL,
  plan       TEXT NOT NULL,                             -- JSON: weights, objectives, rationale
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE writing_submission (
  id          INTEGER PRIMARY KEY,
  task_id     TEXT NOT NULL,
  text        TEXT NOT NULL,
  word_count  INTEGER NOT NULL,
  status      TEXT NOT NULL DEFAULT 'draft',            -- draft | submitted
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE speaking_session (
  id          INTEGER PRIMARY KEY,
  scenario_id TEXT NOT NULL,
  turns       TEXT NOT NULL DEFAULT '[]',               -- JSON: role, text, audio path
  status      TEXT NOT NULL DEFAULT 'active',
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Every AI output keeps its model and prompt version so it can be audited or re-run.
CREATE TABLE ai_feedback (
  id             INTEGER PRIMARY KEY,
  subject_type   TEXT NOT NULL,                         -- writing | speaking | tutor
  subject_id     INTEGER NOT NULL,
  model          TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  result         TEXT NOT NULL,                         -- JSON
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE media_asset (
  id         TEXT PRIMARY KEY,                          -- hash of text + voice
  kind       TEXT NOT NULL,                             -- tts | recording
  path       TEXT NOT NULL,
  source     TEXT NOT NULL,                             -- engine/model or 'learner'
  licence    TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
