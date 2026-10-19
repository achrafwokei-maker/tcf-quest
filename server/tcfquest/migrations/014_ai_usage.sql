-- Online beta: free cloud AI quota used per day by this learner (local Ollama is never counted).
CREATE TABLE IF NOT EXISTS ai_usage (
  day TEXT PRIMARY KEY,                 -- UTC date, matches the provider's daily reset
  neurons REAL NOT NULL DEFAULT 0,      -- Cloudflare Workers AI billing unit (estimated from usage)
  calls INTEGER NOT NULL DEFAULT 0
);
