-- 002: avatar built at onboarding; skins are earned by French level (mastery, never XP).

CREATE TABLE avatar (
  id               INTEGER PRIMARY KEY CHECK (id = 1),   -- single local learner in v1
  gender           TEXT NOT NULL,                         -- woman | man | nonbinary | unspecified
  hair             TEXT NOT NULL,                         -- short | medium | long | curly | braids | bald
  hair_colour      TEXT NOT NULL,                         -- black | brown | auburn | blond | grey | dyed
  skin_tone        INTEGER NOT NULL,                      -- 1 (lightest) .. 6 (deepest)
  facial_hair      TEXT NOT NULL DEFAULT 'none',          -- none | stubble | beard | moustache
  glasses          INTEGER NOT NULL DEFAULT 0,
  vibe             TEXT NOT NULL,                         -- street | classic | sporty | artsy
  description      TEXT NOT NULL DEFAULT '',              -- the learner's own words
  equipped_skin    TEXT NOT NULL DEFAULT 'a1',
  updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
