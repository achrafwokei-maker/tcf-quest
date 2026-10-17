-- 008: writing studio (EE T1–T3): drafts, timed submissions, AI rubric feedback (unofficial estimates).

-- 001 created an unused, always-empty placeholder with this name: replace it.
DROP TABLE IF EXISTS writing_submission;

CREATE TABLE writing_submission (
  id              INTEGER PRIMARY KEY,
  task_id         TEXT NOT NULL,                        -- content/writing task id
  task            TEXT NOT NULL,                        -- EE-T1 | EE-T2 | EE-T3
  mode            TEXT NOT NULL,                        -- training | exam
  text            TEXT NOT NULL DEFAULT '',
  word_count      INTEGER NOT NULL DEFAULT 0,
  status          TEXT NOT NULL DEFAULT 'draft',        -- draft | submitted
  started_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
  submitted_at    TEXT,
  time_limit_s    INTEGER,                              -- exam mode only
  timed_out       INTEGER NOT NULL DEFAULT 0,
  word_range_ok   INTEGER,                              -- deterministic check at submission
  feedback        TEXT,                                 -- validated JSON from the rubric scorer
  feedback_status TEXT NOT NULL DEFAULT 'none',         -- none | pending | done | failed
  feedback_model  TEXT,
  prompt_version  TEXT,
  agreement       TEXT                                  -- high | low (double scoring)
);

CREATE INDEX writing_task_idx ON writing_submission (task_id, status);
