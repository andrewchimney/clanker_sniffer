# worker.py
import os
import json
import asyncio
import asyncpg
import traceback
import logging
import sys

from services import (
    run_demucs,
    run_whisper,
    run_classifier,
    run_acousti,
    wait_for_file,     # sync; we'll wrap with asyncio.to_thread
    preprocess,        # async
)
from utils import (
    SHARED_PATH,
    VOCAL_STEMS_PATH,
    compute_fingerprint_hash,
)
from db import (
    get_and_claim_job,
    mark_job_done,
    mark_job_failed,
    insert_song,
    get_song_by_fingerprint_hash,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app:secret@db:5432/appdb?sslmode=disable")


async def process_job(pool: asyncpg.pool.Pool, conn: asyncpg.Connection, job: asyncpg.Record) -> dict:
    """
    Process one job from job_queue and return the final result dict.
    Uses async HTTP microservices via your services/* helpers.
    """
    # Parse flags
    flags = job["flags"]
    if isinstance(flags, str):
        flags = json.loads(flags or "{}")
    elif flags is None:
        flags = {}

    result = {
        "title": job["title"] or "",
        "artist": job["artist"] or "",
        "lyrics": job["lyrics"] or "",
        "classification": None,
        "accuracy": None,
        "fingerprint": None,
        "fingerprint_hash": None,
        "duration": None,
        "audio_processed": False,
    }

    file_name = job["file_name"]

    # # Convert to WAV if needed (via Acousti /convert)
    # if file_name and not file_name.lower().endswith(".wav"):
    logging.info("proprocess started")
    file_name = await preprocess(file_name)

    # --- IDENTIFICATION (Acousti) ---
    if flags.get("identify") and file_name:
        ac = await run_acousti(file_name)
        matches = ac.get("matches") or []
        if matches:
            top = matches[0]
            result["title"] = top.get("title") or result["title"]
            result["artist"] = top.get("artist") or result["artist"]
        result["fingerprint"] = ac.get("fingerprint")
        result["duration"] = ac.get("duration")
        if result["fingerprint"]:
            result["fingerprint_hash"] = compute_fingerprint_hash(result["fingerprint"])

    # --- EXISTING SONG DEDUPE ---
    existing = None
    if result.get("fingerprint_hash"):
        existing = await get_song_by_fingerprint_hash(conn, result["fingerprint_hash"])

    needs_stem = bool(flags.get("demucs"))
    needs_lyrics = bool(flags.get("whisper"))
    needs_classification = bool(flags.get("classification"))

    if existing:
        needs_stem = needs_stem and not existing.get("audio_processed")
        needs_lyrics = needs_lyrics and not existing.get("lyrics")
        needs_classification = needs_classification and not existing.get("classification")

        if not (needs_stem or needs_lyrics or needs_classification):
            # Serve cached result
            result.update({
                "title": existing["title"],
                "artist": existing["artist"],
                "fingerprint": existing["fingerprint"],
                "duration": existing["duration"],
                "lyrics": existing["lyrics"],
                "classification": existing["classification"],
                "accuracy": existing["accuracy"],
                "audio_processed": existing.get("audio_processed", False),
            })
            return result

        # Seed fields from existing
        result["title"] = existing["title"] or result["title"]
        result["artist"] = existing["artist"] or result["artist"]
        result["fingerprint"] = existing["fingerprint"] or result["fingerprint"]
        result["duration"] = existing["duration"] or result["duration"]

    # --- DEMUCS (stems) ---
    if needs_stem and file_name:
        await run_demucs(file_name)
        # Wait for stem file to appear (same basename under VOCAL_STEMS_PATH)
        await asyncio.to_thread(wait_for_file, os.path.join(VOCAL_STEMS_PATH, file_name))
        result["audio_processed"] = True

    # --- WHISPER (transcribe) ---
    if needs_lyrics and file_name:
        wh = await run_whisper(file_name)
        result["lyrics"] = wh.get("lyrics") or result["lyrics"]

    # --- CLASSIFIER ---
    if needs_classification:
        cl = await run_classifier(result["lyrics"])
        result["classification"] = cl.get("classification")
        result["accuracy"] = cl.get("accuracy")

    # --- PERSIST SONG (if we have a fingerprint) ---
    if result.get("fingerprint_hash"):
        # Your insert_song expects a pool (it acquires internally)
        await insert_song(
            pool,
            title=result["title"],
            artist=result["artist"],
            duration=result["duration"],
            fingerprint=result["fingerprint"],
            fingerprint_hash=result["fingerprint_hash"],
            lyrics=result["lyrics"],
            classification=result["classification"],
            accuracy=result["accuracy"],
            stem_name=file_name,
            audio_processed=result["audio_processed"],
        )

    return result


async def worker_loop():
    pool = await asyncpg.create_pool(dsn=DATABASE_URL)  # include sslmode=disable in DSN if needed
    try:
        while True:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    job = await get_and_claim_job(conn)
                    if not job:
                        # nothing pending; short nap
                        await asyncio.sleep(1.0)
                        continue

                    job_id = job["id"]
                    try:
                        res = await process_job(pool, conn, job)
                        await mark_job_done(conn, job_id, res)
                    except Exception:
                        tb = "".join(traceback.format_exc())
                        await mark_job_failed(conn, job_id, tb[:8000])

            # small throttle so we don't spin too hard
            await asyncio.sleep(0.2)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(worker_loop())
