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

ALTER TABLE songs ADD COLUMN audio_processed BOOLEAN DEFAULT FALSE;

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

ALTER TABLE job_queue
  ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS last_error TEXT,
  ADD COLUMN IF NOT EXISTS queued_at TIMESTAMP DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS started_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS finished_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMP DEFAULT NOW();

-- Pull fastest by ready time
CREATE INDEX IF NOT EXISTS idx_job_queue_ready
  ON job_queue (status, next_attempt_at);

-- Optional: prioritize newest first
CREATE INDEX IF NOT EXISTS idx_job_queue_queued_at
  ON job_queue (queued_at DESC);
