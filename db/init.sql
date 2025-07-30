CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,                    -- Original file name
    artist TEXT,                           -- Optional artist name
    lyrics TEXT,                           -- Transcription from Whisper
    classification TEXT CHECK (
        classification IN ('AI', 'Human')
    ),                                     -- Classification result
    accuracy NUMERIC(5, 4),                -- Confidence score (e.g. 0.9234)
    stem_name TEXT,                       -- Path to the vocal stem file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE songs ADD COLUMN fingerprint TEXT;
ALTER TABLE songs RENAME COLUMN name TO title;
ALTER TABLE songs ADD COLUMN duration INTEGER;  -- Duration in seconds

