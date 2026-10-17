-- 011: strict exam engine (weekly trials, later section and full mocks). Milestone M7.

CREATE TABLE exam_attempt (
  id             INTEGER PRIMARY KEY,
  exam_id        TEXT NOT NULL,                       -- content/exams/exams.json id
  kind           TEXT NOT NULL,                       -- weekly | section | full
  status         TEXT NOT NULL DEFAULT 'in_progress', -- in_progress | completed
  section_index  INTEGER NOT NULL DEFAULT 0,
  sections       TEXT NOT NULL,                       -- JSON: plan + per-section state
  answers        TEXT NOT NULL DEFAULT '{}',          -- JSON {item_id: {response, at}}
  plays          TEXT NOT NULL DEFAULT '{}',          -- JSON {item_id: n} (listening: one play)
  started_at     TEXT NOT NULL,
  completed_at   TEXT,
  results        TEXT,                                -- JSON, deterministic scoring (CO/CE) + EE/EO links
  report         TEXT                                 -- JSON, post-exam analysis (M9)
);
