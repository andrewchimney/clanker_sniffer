import os
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional


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
    stem_name: str
):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO songs (
                title, artist, duration, fingerprint, fingerprint_hash,
                lyrics, classification, accuracy, stem_name
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (fingerprint_hash) DO NOTHING
        """, title, artist, duration, fingerprint, fingerprint_hash,
             lyrics, classification, accuracy, stem_name)


async def get_song_by_fingerprint_hash(pool, fingerprint_hash: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM songs WHERE fingerprint_hash = $1", fingerprint_hash)
        return dict(row) if row else None
