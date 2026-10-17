-- 006: mistake notebook linked to content, review notes for the learner.

ALTER TABLE mistake ADD COLUMN set_id TEXT;                          -- source exercise set of item_id
ALTER TABLE mistake ADD COLUMN review_note TEXT NOT NULL DEFAULT ''; -- reason given when a dispute was rejected
CREATE UNIQUE INDEX mistake_item_idx ON mistake (item_id);
ALTER TABLE mastery ADD COLUMN unhinted_correct INTEGER NOT NULL DEFAULT 0; -- at least one correct answer without help
