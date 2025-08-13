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

ALTER TABLE songs ADD COLUMN fingerprint_hash TEXT;
UPDATE songs SET fingerprint_hash = md5(fingerprint);

ALTER TABLE songs ADD CONSTRAINT unique_fingerprint_hash UNIQUE(fingerprint_hash);

ALTER TABLE songs ADD COLUMN audio_processed BOOLEAN DEFAULT FALSE

CREATE TABLE job_queue (
    id SERIAL PRIMARY KEY,
    status TEXT DEFAULT 'pending',  -- pending | processing | done | failed
    input_type TEXT NOT NULL,
    title TEXT,
    artist TEXT,
    file_name TEXT,
    lyrics TEXT,
    flags JSONB NOT NULL,
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_job_queue_timestamp
BEFORE UPDATE ON job_queue
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

