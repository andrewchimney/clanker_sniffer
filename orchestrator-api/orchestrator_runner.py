import json
from fastapi import FastAPI, HTTPException, UploadFile, Form, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.concurrency import run_in_threadpool
import os
from contextlib import asynccontextmanager
from typing import List, Optional
import asyncio
import asyncpg
import time
from services import (
    run_demucs, 
    run_whisper, 
    run_classify, 
    run_acousti,
    preprocess
)
from utils import (
    SHARED_PATH, 
    STEMS_PATH, 
    RAW_PATH,
    FRONTEND_ORIGIN, 
    save_uploaded_file, 
    compute_fingerprint_hash
)
from db import (
    update_job,
    lifespan,
    upsert_song,
    get_song_by_fingerprint_hash,
    get_song_by_title_artist,
    dsn,
    create_job,
    get_job
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-9s %(message)s",
)
logger = logging.getLogger("orchestrator")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    app.state.db_pool = await asyncpg.create_pool(dsn=dsn)

    # create a stop event that signals workers to exit
    app.state.stop_event = asyncio.Event()

    # Optionally run multiple workers for concurrency
    worker_count = 1  # bump if you want N workers
    app.state.worker_tasks = [
        asyncio.create_task(worker_loop(app.state.db_pool, app.state.stop_event))
        for _ in range(worker_count)
    ]

    try:
        # Yield control back to FastAPI—startup completes immediately (non-blocking)
        yield
    finally:
        # --- Shutdown ---
        # signal workers to stop and wait them out
        app.state.stop_event.set()
        for t in app.state.worker_tasks:
            t.cancel()
        # gather with return_exceptions=True so one CancelledError doesn't abort others
        await asyncio.gather(*app.state.worker_tasks, return_exceptions=True)

        await app.state.db_pool.close()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def worker_loop(pool: asyncpg.Pool, stop: asyncio.Event, poll_interval: float = 0.5):
    logger.info("worker_loop starting")
    try:
        while not stop.is_set():
            async with pool.acquire() as conn:
                try:
                    job = await process_job(conn)
                except Exception as e:
                    # DB hiccup: brief backoff, keep loop healthy
                    await asyncio.sleep(1.0)
                    continue

                if not job:
                    # No work right now; wait a bit, but wake up early if stopping
                    try:
                        await asyncio.wait_for(stop.wait(), timeout=poll_interval)
                    except asyncio.TimeoutError:
                        pass
                    continue
                
    except asyncio.CancelledError:
        # Allow task cancellation to be graceful
        pass
    finally:
        logger.info("worker_loop exiting")

async def process_job(conn):
    """
    Claims one job, runs exactly one needed stage based on want/done flags,
    then advances (or completes) the job. Returns (job_id, stage) or None if no work.
    """
    job = await get_and_claim_job(conn)
    if not job:
        return None
    logger.info("🟦Processing Job🟦")
    try:
        stage = job["current_stage"]
        file_path= job["file_path"]
        if not stage:
            # Nothing to do — finalize as complete just in case
            await conn.execute("UPDATE jobs SET status='Complete' WHERE id=$1", job["id"])
            return None
        # Run one stage
        if stage == "identify":
            acousti_out = await run_acousti(file_path)
            
            matches = acousti_out.get("matches", [])
            title = matches[0].get("title") if matches else "Unknown"
            artist = matches[0].get("artist") if matches else "Unknown"

            await update_job(
                conn,
                job_id=job["id"],
                title=title,
                artist=artist,
                duration=acousti_out.get("duration"),
                fingerprint=acousti_out.get("fingerprint"),
                fingerprint_hash=compute_fingerprint_hash(acousti_out.get("fingerprint")),
                file_path=acousti_out.get("file_path"),
                done_identify= True,
                status="Not Started",
                current_stage="demucs"
            )
               
        elif stage == "demucs":
            demucs_out = await run_demucs(file_path)
            
            await update_job(
                conn,
                job_id=job["id"],
                file_path=demucs_out.get("file_path"),
                done_demucs= True,
                status="Not Started",
                current_stage="whisper"
            )
            
            
        elif stage == "whisper":
            whisper_out = await run_whisper(file_path)
            
            await update_job(
                conn,
                lyrics = whisper_out.get("lyrics"),
                job_id=job["id"],
                done_whisper= True,
                status="Not Started",
                current_stage="classify"
            )
            
            
        elif stage == "classify":
            lyrics=job["lyrics"]
            classify_out = await run_classify(lyrics)
            
            await update_job(
                conn,
                job_id=job["id"],
                done_classify= True,
                classification= classify_out.get("classification"),
                accuracy= classify_out.get("accuracy"),
                status="Not Started",
                current_stage="None"
            )
        else:
            raise RuntimeError(f"Unknown stage: {stage}")
        
        logger.info("🟦Job Processed Successfully🟦")
        song_id = await finalize_job_if_ready(conn, job["id"])
        if song_id:
            return ("completed", song_id)   # promoted to songs; job was deleted
        else:
            return ("in_progress", job["id"])  # more stages remain

    except Exception as e:
        print(e)
        # Simple failure path; you can expand to backoff logic as needed
        await conn.execute(
            "UPDATE jobs SET status='Failed' WHERE id=$1",
            job["id"],
        )
        raise

def job_is_complete(job: dict) -> bool:
    """A job is complete when every wanted stage is done."""
    wants_dones = [
        ("identify", job["want_identify"], job["done_identify"]),
        ("demucs",   job["want_demucs"],   job["done_demucs"]),
        ("whisper",  job["want_whisper"],  job["done_whisper"]),
        ("classify", job["want_classify"], job["done_classify"]),
    ]
    return all((not want) or done for _, want, done in wants_dones)

async def finalize_job_if_ready(conn, job_id: int) -> int | None:
    """
    If the job has completed all requested stages:
      1) INSERT its data into songs
      2) DELETE the job
    Returns the new song_id (or existing song_id if already set), else None.
    """
    logger.info("🟦looking to see if request is complete")
    job = await conn.fetchrow("SELECT * FROM jobs WHERE id=$1 FOR UPDATE", job_id)
    
    if not job:
        return None

    if not job_is_complete(job):
        return None
    
    logger.info("🟦Request Complete, Adding to Database")
    


    async with conn.transaction():
    # lock the job row
        job = await conn.fetchrow("SELECT * FROM jobs WHERE id=$1 FOR UPDATE", job_id)
        if not job or not job_is_complete(job):
            return None

        # build params for upsert_song from the job
        

        song_fields = {
            "title": job["title"],
            "artist": job["artist"],
            "duration": int(job["duration"]) if job["duration"] is not None else None,
            "fingerprint": job["fingerprint"],
            "fingerprint_hash": job["fingerprint_hash"],
            "lyrics": job["lyrics"],
            "classification": job["classification"],
            "accuracy": float(job["accuracy"]) if job["accuracy"] is not None else None,
            "file_path": job["file_path"],
            "audio_processed": bool(job["audio_processed"]),
        }

    song_id = await upsert_song(conn, **song_fields)
    await conn.execute("DELETE FROM jobs WHERE id=$1", job_id)



    logger.info("🟦Request Successfully Added to Database🟦")
    return song_id

async def get_and_claim_job(conn):
    """
    Atomically pick ONE pending job and mark it 'Claimed' with the next current_stage.
    Uses SKIP LOCKED so multiple workers don't collide.
    """
    sql = """
    WITH candidate AS (
      SELECT j.id,
             CASE
               WHEN j.want_identify AND NOT j.done_identify THEN 'identify'
               WHEN j.want_demucs   AND NOT j.done_demucs   THEN 'demucs'
               WHEN j.want_whisper  AND NOT j.done_whisper  THEN 'whisper'
               WHEN j.want_classify AND NOT j.done_classify THEN 'classify'
               ELSE NULL
             END AS next_stage
      FROM jobs j
      WHERE j.status IN ('Not Started','Queued','In Progress')
        AND (
          (j.want_identify AND NOT j.done_identify) OR
          (j.want_demucs   AND NOT j.done_demucs)   OR
          (j.want_whisper  AND NOT j.done_whisper)  OR
          (j.want_classify AND NOT j.done_classify)
        )
      ORDER BY j.id
      FOR UPDATE SKIP LOCKED
      LIMIT 1
    ),
    upd AS (
      UPDATE jobs j
      SET status = 'Claimed',
          current_stage = c.next_stage
      FROM candidate c
      WHERE j.id = c.id
      RETURNING j.*
    )
    SELECT * FROM upd;
    """
    row = await conn.fetchrow(sql)
    return dict(row) if row else None


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/songs")
async def list_songs(request: Request):
    try:
        pool = request.app.state.db_pool
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM songs ORDER BY created_at DESC")
            result = [dict(row) for row in rows]
            return JSONResponse(status_code=200, content=jsonable_encoder(result))
    except Exception as e:
        print("❌ DB error in GET /songs:", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Database error"}
        )

@app.get("/api/jobs/{job_id}")
async def get_job(request: Request, job_id: int):
    try:
        pool = request.app.state.db_pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
            if not row:
                raise HTTPException(status_code=404, detail="Job not found")

            return JSONResponse(
                status_code=200,
                content=jsonable_encoder(dict(row))
            )
    except HTTPException:
        raise
    except Exception as e:
        print("❌ DB error in GET /jobs/{job_id}:", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Database error"}
        )

@app.post("/api/analyze")
async def analyze(
    request: Request,
    input_type: str = Form(...),
    audio: Optional[UploadFile] = File(None),
    outputs: List[str] = Form(...),
    title: str = Form(""),
    artist: str = Form(""),
    lyrics: str = Form("")
):
    try:
    
        db_pool = request.app.state.db_pool
        
        want_identify     = "identify" in outputs
        want_demucs       = "stems" in outputs 
        want_whisper      = "lyrics" in outputs
        want_classify     = "classification" in outputs
        
        current_stage = None
        
        if input_type=="audio":
            if not audio:
                return {"success": False, "error": "Missing audio file for input_type 'audio'"}
            raw_filename=save_uploaded_file(audio)
            file_path = os.path.join(RAW_PATH, raw_filename)


        if input_type == "search":
            if not title or not artist:
                return {"success": False, "error": "Missing title or artist for search input"}

            #existing = await get_song_by_title_artist(db_pool, title, artist)

            # if not existing:
            #     return {"success": False, "error": "Song not found in database"}
            
            # return {"success": True, "song": existing}

        
        job_id = await create_job(
            db_pool,
            title=title,
            artist=artist,
            lyrics=lyrics,
            input_type=input_type,
            current_stage=current_stage,
            file_path=file_path,
            want_identify=want_identify, 
            want_demucs=want_demucs, 
            want_whisper=want_whisper, 
            want_classify=want_classify
)
        return {"success": True, "job_id": job_id}
    except Exception as e:
        print(str(e))
        return {"success": False, "error": str(e)}
    