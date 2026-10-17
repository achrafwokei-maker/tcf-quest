-- 007: concept-level weaknesses (Detect → Diagnose → Teach → Practise → Retest → Confirm → Adapt).
-- One row per primary competency. Item-level review scheduling stays in `mistake`.

CREATE TABLE weakness (
  competency     TEXT PRIMARY KEY,                     -- e.g. gram.conditionnel-politesse
  skill          TEXT NOT NULL,                        -- listening | reading | speaking | writing
  task           TEXT,                                 -- TCF section/task it was seen in, e.g. EO-T2 or CO
  category       TEXT NOT NULL,                        -- grammar | vocabulary | comprehension | expression
  cause          TEXT NOT NULL DEFAULT 'unknown',      -- french | technique | timing | unknown (set by exam reports)
  state          TEXT NOT NULL DEFAULT 'detected',     -- detected | training | improving | retest_due | mastered
  frequency      INTEGER NOT NULL DEFAULT 0,           -- wrong or partial answers observed
  correct_days   TEXT NOT NULL DEFAULT '[]',           -- days with an unhinted correct answer since the last error
  severity       REAL NOT NULL DEFAULT 0,              -- 0..1
  confidence     TEXT NOT NULL DEFAULT 'low',          -- low | medium | high (how sure the diagnosis is)
  examples       TEXT NOT NULL DEFAULT '[]',           -- last 5 errors {item, answer, correction, date}
  items_failed   TEXT NOT NULL DEFAULT '[]',           -- distinct item refs answered wrongly
  interventions  TEXT NOT NULL DEFAULT '[]',           -- {kind, date, item?, outcome?}
  retests        TEXT NOT NULL DEFAULT '[]',           -- {item, date, verdict}
  retest_item    TEXT,                                 -- '<set>--<item>' never answered before
  needs_content  INTEGER NOT NULL DEFAULT 0,           -- 1 = no unseen question exists yet for the retest
  rethink        INTEGER NOT NULL DEFAULT 0,           -- 1 = retests failed twice: change the teaching approach
  reopen_count   INTEGER NOT NULL DEFAULT 0,
  first_seen     TEXT NOT NULL,
  last_seen      TEXT NOT NULL,
  mastered_at    TEXT
);

CREATE INDEX weakness_state_idx ON weakness (state, severity);
