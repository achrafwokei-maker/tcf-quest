-- 003: richer attempts for the exercise engine (blueprint I.4).

ALTER TABLE attempt ADD COLUMN verdict TEXT;                               -- correct | partial | incorrect | skipped
ALTER TABLE attempt ADD COLUMN evidence_weight REAL NOT NULL DEFAULT 0;    -- how much this attempt counts as evidence
ALTER TABLE attempt ADD COLUMN flags TEXT NOT NULL DEFAULT '[]';           -- JSON: audio_off, hint, slow_audio, requeue...
