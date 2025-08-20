import os
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
import json

dsn = os.getenv("DATABASE_URL")


@asynccontextmanager
async def lifespan(app):
    app.state.db_pool = await asyncpg.create_pool(dsn=dsn)
    yield
    await app.state.db_pool.close()


async def insert_song(
    pool,
    title: str,
    artist: str,
    duration: Optional[float],
    fingerprint: Optional[str],
    fingerprint_hash: str,
    lyrics: Optional[str],
    classification: Optional[str],
    accuracy: Optional[float],
    stem_name: str,
    audio_processed: bool
):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO songs (
                title, artist, duration, fingerprint, fingerprint_hash,
                lyrics, classification, accuracy, stem_name, audio_processed
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
               ON CONFLICT (fingerprint_hash) DO UPDATE SET
                title = EXCLUDED.title,
                artist = EXCLUDED.artist,
                duration = EXCLUDED.duration,
                fingerprint = EXCLUDED.fingerprint,
                lyrics = EXCLUDED.lyrics,
                classification = EXCLUDED.classification,
                accuracy = EXCLUDED.accuracy,
                stem_name = EXCLUDED.stem_name,
                audio_processed = EXCLUDED.audio_processed
        """, title, artist, duration, fingerprint, fingerprint_hash,
             lyrics, classification, accuracy, stem_name, audio_processed)

async def get_song_by_fingerprint_hash(pool, fingerprint_hash: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM songs WHERE fingerprint_hash = $1", fingerprint_hash)
        return dict(row) if row else None
    
async def get_song_by_title_artist(pool, title, artist):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM songs
            WHERE LOWER(title) = LOWER($1) AND LOWER(artist) = LOWER($2)
            LIMIT 1
        """, title, artist)
        return dict(row) if row else None


async def insert_job(
    conn: asyncpg.Connection,
    input_type: str,
    title: Optional[str],
    artist: Optional[str],
    file_name: Optional[str],
    lyrics: Optional[str],
    flags: dict
) -> int:
    """
    Inserts a job into the job_queue table and returns the new job ID.
    """
    query = """
        INSERT INTO job_queue (input_type, title, artist, file_name, lyrics, flags)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id;
    """
    job_id = await conn.fetchval(query, input_type, title, artist, file_name, lyrics, json.dumps(flags))
    return job_id

async def get_and_claim_job(conn):
    return await conn.fetchrow("""
        UPDATE job_queue
        SET status = 'processing', updated_at = NOW()
        WHERE id = (
            SELECT id FROM job_queue
            WHERE status = 'pending'
            ORDER BY created_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING *;
    """)
    
async def mark_job_done(conn, job_id: int, result: dict):
    await conn.execute("""
        UPDATE job_queue
        SET status = 'done',
            result = $1,
            updated_at = NOW()
        WHERE id = $2
    """, json.dumps(result), job_id)
    
async def mark_job_failed(conn, job_id: int, error_msg: str):
    await conn.execute("""
        UPDATE job_queue
        SET status = 'failed',
            last_error = $1,
            updated_at = NOW()
        WHERE id = $2
    """, error_msg, job_id)
    
async def get_job_status(conn, job_id: int):
    return await conn.fetchrow("""
        SELECT status, result, error FROM job_queue WHERE id = $1
    """, job_id)
    
async def setup_db_pool(dsn: str):
    return await asyncpg.create_pool(dsn)

