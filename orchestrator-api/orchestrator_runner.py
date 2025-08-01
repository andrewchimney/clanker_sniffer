from fastapi import FastAPI, UploadFile, Form, File
import os
from fastapi.concurrency import run_in_threadpool
import sys
from contextlib import asynccontextmanager
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from typing import List
from db import lifespan, insert_song, get_song_by_fingerprint_hash
from services import (
    run_demucs, run_whisper, run_classifier, run_acousti,
    wait_for_file, preprocess
)
from utils import SHARED_PATH, VOCAL_STEMS_PATH, FRONTEND_ORIGIN, save_uploaded_file, compute_fingerprint_hash


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

@app.post("/api/analyze")
async def analyze(
    request: Request,
    input_type: str = Form(...),
    audio: UploadFile = File(...),
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
    result = {
        "title": None,
        "artist": None,
        "lyrics": None,
        "classification": None,
        "accuracy": None,
        "fingerprint": None,
        "duration": None,
    }


    try:

        if input_type == "audio":
            # Always need to save file
            raw_filename = save_uploaded_file(audio)
            file_name = preprocess(raw_filename)

            # 🔍 Song Identification
            if flags["identify"]:
                acousti_out = await run_in_threadpool(run_acousti, file_name)
                matches = acousti_out.get("matches", [])
                if matches:
                    result["title"] = matches[0].get("title")
                    result["artist"] = matches[0].get("artist")
                else:
                    result["title"] = "Unknown"
                    result["artist"] = "Unknown"

                result["fingerprint"] = acousti_out.get("fingerprint")
                result["fingerprint_hash"] = compute_fingerprint_hash(result["fingerprint"])
                result["duration"] = acousti_out.get("duration")

                # Check if song already in DB
                existing = await get_song_by_fingerprint_hash(db_pool, result["fingerprint_hash"])
                if existing:
                    print("✅ Found existing song in DB, skipping processing")
                    os.remove(os.path.join(SHARED_PATH, file_name))
                    return {
                        "success": True,
                        "result": {
                            "title": existing["title"],
                            "artist": existing["artist"],
                            "fingerprint": existing["fingerprint"],
                            "duration": existing["duration"],
                            "lyrics": existing["lyrics"],
                            "classification": existing["classification"],
                            "accuracy": existing["accuracy"],
                        },
                        "cached": True,
                    }

        # 🎛️ Demucs + Whisper
        if flags["demucs"]:
            await run_in_threadpool(run_demucs, file_name)
            wait_for_file(os.path.join(VOCAL_STEMS_PATH, file_name))

        if flags["whisper"]:
            whisper_out = await run_in_threadpool(run_whisper, file_name)
            result["lyrics"] = whisper_out.get("lyrics")

        # 🤖 Classification
        if flags["classification"]:
            classifier_out = await run_in_threadpool(run_classifier, result["lyrics"])
            result["classification"] = classifier_out.get("classification")
            result["accuracy"] = classifier_out.get("accuracy")

        # 📝 Save to DB if audio-based
        print("✅ Processing finished, adding to db")
        if input_type == "audio":
            await insert_song(
                db_pool,
                title=result["title"],
                artist=result["artist"],
                duration=result["duration"],
                fingerprint=result["fingerprint"],
                fingerprint_hash=result["fingerprint_hash"],
                lyrics=result["lyrics"],
                classification=result["classification"],
                accuracy=result["accuracy"],
                stem_name=file_name,
            )
            
            
        # if flags["demucs"]:
        #     await run_in_threadpool(run_demucs, file_name)
        #     wait_for_file(os.path.join(VOCAL_STEMS_PATH, file_name))
        #     whisper_out = run_whisper(file_name)
        #     result["lyrics"] = whisper_out.get("lyrics")
            
        # if flags[""]:
        #     await run_in_threadpool(run_demucs, file_name)
        #     wait_for_file(os.path.join(VOCAL_STEMS_PATH, file_name))
        #     whisper_out = run_whisper(file_name)
        #     result["lyrics"] = whisper_out.get("lyrics")
            
            
            
        # elif mode == "demucs-whisper-classifier":
        #     acousti_out = run_in_threadpool(run_acousti,file_name)
        #     matches = acousti_out.get("matches", [])
            
        #     if matches:
        #         result["title"] = matches[0].get("title")
        #         result["artist"] = matches[0].get("artist") 
        #     else:
        #         result["title"] = "Unknown"
        #         result["artist"] = "Unknown"
        #     result["fingerprint"] = acousti_out.get("fingerprint")
        #     result["fingerprint_hash"] = compute_fingerprint_hash(result["fingerprint"])
        #     result["duration"] = acousti_out.get("duration")
            
        #     existing = await get_song_by_fingerprint_hash(db_pool, result["fingerprint_hash"])
        #     if existing:
        #         print("✅ Found existing song in DB, skipping processing")
        #         os.remove(f"/shared_data/{file_name}")
        #         return {
        #             "success": True,
        #             "result": {
        #                 "title":existing["title"],
        #                 "artist": existing["artist"],
        #                 "fingerprint": existing["fingerprint"],
        #                 "duration": existing["duration"],
        #                 "lyrics": existing["lyrics"],
        #                 "classification": existing["classification"],
        #                 "accuracy": existing["accuracy"],
        #             },
        #             "cached": True
        #         }
        #     run_in_threadpool(run_demucs, file_name)
        #     wait_for_file(os.path.join(VOCAL_STEMS_PATH, file_name))
        #     whisper_out = run_in_threadpool(run_whisper,file_name)
        #     result["lyrics"] = whisper_out.get("lyrics")
        #     classifier_out = run_classifier(result["lyrics"])
        #     result["classification"] = classifier_out.get("classification")
        #     result["accuracy"] = classifier_out.get("accuracy")
        # elif mode == "classifier-text":
        #     classifier_out = run_in_threadpool(run_classifier,lyrics)
        #     result["classification"] = classifier_out.get("classification")
        #     result["accuracy"] = classifier_out.get("accuracy")
        # else:
        #     return {"success": False, "error": f"Invalid mode: {mode}"}

        await insert_song(
            db_pool,
            title=result["title"],
            artist=result["artist"],
            duration=result["duration"],
            fingerprint=result["fingerprint"],
            fingerprint_hash=result["fingerprint_hash"],
            lyrics=result["lyrics"],
            classification=result["classification"],
            accuracy=result["accuracy"],
            stem_name=file_name
        )
        
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "error": str(e)}
    