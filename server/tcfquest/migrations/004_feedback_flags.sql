-- 004: learner feedback on answers (blueprint "Feedback system") and the review queue.

CREATE TABLE feedback_flag (
  id              INTEGER PRIMARY KEY,
  attempt_id      INTEGER NOT NULL REFERENCES attempt(id),
  item_id         TEXT NOT NULL,
  kind            TEXT NOT NULL,              -- too_easy | too_hard | unclear | dispute | technical
  note            TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL,              -- noted (no review needed) | open | accepted | rejected
  original_weight REAL,                       -- evidence weight before a dispute/technical flag removed it
  resolution_note TEXT NOT NULL DEFAULT '',
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at     TEXT,
  UNIQUE (attempt_id, kind)
);
CREATE INDEX feedback_flag_status_idx ON feedback_flag (status, kind);
CREATE INDEX feedback_flag_item_idx ON feedback_flag (item_id, kind);

-- Answers accepted after review; the checker treats them as correct from then on.
-- response_key: option id (choice), normalized text (type), normalized tiles joined by spaces (arrange).
CREATE TABLE accepted_answer (
  item_id        TEXT NOT NULL,
  response_key   TEXT NOT NULL,
  source_flag_id INTEGER REFERENCES feedback_flag(id),
  accepted_at    TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (item_id, response_key)
);
