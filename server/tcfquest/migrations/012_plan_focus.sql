-- 012: what each assessment changes in the next week's plan (milestone M9).

CREATE TABLE plan_focus (
  attempt_id  INTEGER PRIMARY KEY,                    -- exam_attempt that produced it
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  valid_until TEXT NOT NULL,                          -- date: 7 days after the assessment
  focus       TEXT NOT NULL,                          -- JSON [{skill, competencies[], weight, reason}]
  complete    INTEGER NOT NULL DEFAULT 0              -- 1 once writing/speaking feedback was included
);
