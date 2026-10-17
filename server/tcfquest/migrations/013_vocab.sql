-- 013: vocabulary cards by communicative function, with a spaced-repetition schedule.
-- A retention aid only: it never feeds skill estimates or weaknesses.
CREATE TABLE vocab_progress (
  card_id    TEXT PRIMARY KEY,
  box        INTEGER NOT NULL DEFAULT 0,      -- 0..5 = consecutive successful recalls (5 = mastered)
  due        TEXT NOT NULL,                   -- ISO date
  reps       INTEGER NOT NULL DEFAULT 0,
  lapses     INTEGER NOT NULL DEFAULT 0,      -- times forgotten
  first_seen TEXT NOT NULL,
  last_seen  TEXT NOT NULL
);
CREATE INDEX vocab_due_idx ON vocab_progress (due);
