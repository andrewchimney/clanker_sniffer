CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,               -- Song name
    artist TEXT,                      -- Artist name (optional)
    lyrics TEXT,                      -- May be null if not transcribed
    classification TEXT,             -- "AI" or "Human" (nullable if not run)
    accuracy FLOAT,                   -- Confidence score (nullable)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
