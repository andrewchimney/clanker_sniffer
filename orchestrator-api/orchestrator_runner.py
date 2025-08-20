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
from services import (
    run_demucs, 
    run_whisper, 
    run_classifier, 
    run_acousti,
    wait_for_file, 
    preprocess
)
from utils import (
    SHARED_PATH, 
    VOCAL_STEMS_PATH, 
    FRONTEND_ORIGIN, 
    save_uploaded_file, 
    compute_fingerprint_hash
)
from db import (
    lifespan,
    get_and_claim_job,
    mark_job_done,
    mark_job_failed,
    insert_song,
    get_song_by_fingerprint_hash,
    get_song_by_title_artist,
    dsn
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.db_pool = await asyncpg.create_pool(dsn=dsn)

    try:
        yield
    finally:
        # cleanup
        await app.state.db_pool.close()



app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        
        
        
@app.post("/api/analyze", status_code=202)
async def enqueue_analyze(
    request: Request,
    input_type: str = Form(...),
    audio: Optional[UploadFile] = File(None),
    outputs: List[str] = Form(...),
    title: str = Form(""),
    artist: str = Form(""),
    lyrics: str = Form("")
):
    db_pool = request.app.state.db_pool

    flags = {
        "identify": "identify" in outputs,
        "demucs": "vocals" in outputs or "lyrics" in outputs or "classification" in outputs,
        "whisper": "lyrics" in outputs or "classification" in outputs,
        "classification": "classification" in outputs,
    }

    file_name = None
    if input_type == "audio":
        if not audio:
            raise HTTPException(400, "Missing audio file for input_type 'audio'")
        raw_filename = save_uploaded_file(audio)          # your existing helper
        file_name = raw_filename            

    async with db_pool.acquire() as con:
        job_id = await con.fetchval(
            """
            INSERT INTO job_queue (status, input_type, title, artist, file_name, lyrics, flags)
            VALUES ('pending', $1, NULLIF($2, ''), NULLIF($3, ''), $4, NULLIF($5, ''), $6::jsonb)
            RETURNING id
            """,
            input_type, title, artist, file_name, lyrics, json.dumps(flags)
        )

    return JSONResponse({"enqueued": True, "job_id": job_id}, status_code=202)


@app.get("/api/jobs/{job_id}")
async def get_job(request: Request, job_id: int):
    db_pool = request.app.state.db_pool
    async with db_pool.acquire() as con:
        row = await con.fetchrow("SELECT * FROM job_queue WHERE id=$1", job_id)
    if not row:
        raise HTTPException(404, "Job not found")
    return dict(row)

# @app.post("/api/analyze")
# async def analyze(
#     request: Request,
#     input_type: str = Form(...),
#     audio: Optional[UploadFile] = File(None),
#     outputs: List[str] = Form(...),
#     title: str = Form(""),
#     artist: str = Form(""),
#     lyrics: str = Form("")
# ):
#     db_pool = request.app.state.db_pool
#     flags = {
#         "identify": "identify" in outputs,
#         "demucs": "vocals" in outputs or "lyrics" in outputs or "classification" in outputs,
#         "whisper": "lyrics" in outputs or "classification" in outputs,
#         "classification": "classification" in outputs,
#     }

#     result = {
#         "title": title,
#         "artist": artist,
#         "lyrics": lyrics,
#         "classification": None,
#         "accuracy": None,
#         "fingerprint": None,
#         "duration": None,
#         "audio_processed": False
#     }

#     try:
#         if input_type == "audio":
#             if not audio:
#                 return {"success": False, "error": "Missing audio file for input_type 'audio'"}
#             raw_filename = save_uploaded_file(audio)
#             file_name = preprocess(raw_filename)
            
#         if input_type == "search":
#             if not title or not artist:
#                 return {"success": False, "error": "Missing title or artist for search input"}

#             existing = await get_song_by_title_artist(db_pool, title, artist)

#             if not existing:
#                 return {"success": False, "error": "Song not found in database"}

#             result["title"] = existing["title"]
#             result["artist"] = existing["artist"]
#             result["fingerprint"] = existing["fingerprint"]
#             result["fingerprint_hash"] = existing["fingerprint_hash"]
#             result["duration"] = existing["duration"]

#         # 🔍 Song Identification
#         if flags["identify"]:
#             acousti_out = await run_in_threadpool(run_acousti, file_name)
#             matches = acousti_out.get("matches", [])
#             if matches:
#                 result["title"] = matches[0].get("title")
#                 result["artist"] = matches[0].get("artist")
#             else:
#                 result["title"] = result["title"] or "Unknown"
#                 result["artist"] = result["artist"] or "Unknown"

#             result["fingerprint"] = acousti_out.get("fingerprint")
#             result["fingerprint_hash"] = compute_fingerprint_hash(result["fingerprint"])
#             result["duration"] = acousti_out.get("duration")

#         # Check if song already in DB
#         existing = None
#         if result.get("fingerprint_hash"):
#             existing = await get_song_by_fingerprint_hash(db_pool, result["fingerprint_hash"])

#         needs_stem = flags["demucs"]
#         needs_lyrics = flags["whisper"]
#         needs_classification = flags["classification"]

#         if existing:
#             needs_stem = flags["demucs"] and not existing.get("audio_processed")
#             needs_lyrics = flags["whisper"] and not existing.get("lyrics")
#             needs_classification = flags["classification"] and not existing.get("classification")

#             if not (needs_stem or needs_lyrics or needs_classification):
#                 print("✅ Found complete existing song in DB, skipping processing")
#                 if input_type == "audio":
#                     os.remove(os.path.join(SHARED_PATH, file_name))
#                 return {
#                     "success": True,
#                     "result": {
#                         "title": existing["title"],
#                         "artist": existing["artist"],
#                         "fingerprint": existing["fingerprint"],
#                         "duration": existing["duration"],
#                         "lyrics": existing["lyrics"],
#                         "classification": existing["classification"],
#                         "accuracy": existing["accuracy"],
#                     },
#                     "cached": True,
#                 }

#             result["title"] = existing["title"]
#             result["artist"] = existing["artist"]
#             result["fingerprint"] = existing["fingerprint"]
#             result["duration"] = existing["duration"]

#         # 🎛️ Demucs
#         if needs_stem:
#             print("🎛️ Running Demucs...")
#             await run_in_threadpool(run_demucs, file_name)
#             wait_for_file(os.path.join(VOCAL_STEMS_PATH, file_name))
#             result["audio_processed"] = True

#         # 📝 Whisper
#         if needs_lyrics:
#             print("📝 Running Whisper...")
#             whisper_out = await run_in_threadpool(run_whisper, file_name)
#             result["lyrics"] = whisper_out.get("lyrics")

#         # 🤖 Classification
#         if needs_classification:
#             print("🤖 Running Classifier...")
#             classifier_out = await run_in_threadpool(run_classifier, result["lyrics"])
#             result["classification"] = classifier_out.get("classification")
#             result["accuracy"] = classifier_out.get("accuracy")

#         print("🜥 Processing finished")

#         if input_type in {"audio", "search"} and result.get("fingerprint_hash"):
#             print("⬜ adding to db")
#             print(result)
#             await insert_song(
#                 db_pool,
#                 title=result["title"],
#                 artist=result["artist"],
#                 duration=result["duration"],
#                 fingerprint=result["fingerprint"],
#                 fingerprint_hash=result["fingerprint_hash"],
#                 lyrics=result["lyrics"],
#                 classification=result["classification"],
#                 accuracy=result["accuracy"],
#                 stem_name=file_name if input_type == "audio" else None,
#                 audio_processed=result["audio_processed"]
#             )

#         print("🜥 analyze call successful")
#         return {"success": True, "result": result}

#     except Exception as e:
#         return {"success": False, "error": str(e)}


