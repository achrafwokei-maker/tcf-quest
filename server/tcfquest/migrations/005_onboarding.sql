-- 005: conversational onboarding (blueprint B + Part II R1–R6).

-- In-progress onboarding: autosaved after every step so it resumes exactly.
CREATE TABLE onboarding (
  id           INTEGER PRIMARY KEY CHECK (id = 1),
  step         TEXT NOT NULL DEFAULT 'language',
  answers      TEXT NOT NULL DEFAULT '{}',           -- JSON
  started_at   TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at TEXT
);

-- New profile facts. Self-rating and concern are never treated as measurements.
ALTER TABLE profile ADD COLUMN target_nclc_by_skill TEXT;          -- JSON {listening, reading, speaking, writing} or NULL
ALTER TABLE profile ADD COLUMN exam_window TEXT;                   -- lt1m | 3m | 6m | later | undecided
ALTER TABLE profile ADD COLUMN plan_mode TEXT;                     -- final_review | sprint | balanced | learning_first
ALTER TABLE profile ADD COLUMN self_rating INTEGER;                -- 1..5, picks starting content only
ALTER TABLE profile ADD COLUMN concern_section TEXT;               -- listening | reading | speaking | writing | NULL
ALTER TABLE profile ADD COLUMN learning_preference TEXT;           -- short | conversation | explanations | timed | balanced
ALTER TABLE profile ADD COLUMN start_route TEXT;                   -- evaluate | train
ALTER TABLE profile ADD COLUMN exam_briefing_done INTEGER NOT NULL DEFAULT 0;
