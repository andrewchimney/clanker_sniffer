from fastapi import FastAPI, UploadFile, Form, File
import shutil
import os
import uuid
import requests
import subprocess
from pathlib import Path
import time
import sys
from contextlib import asynccontextmanager
import asyncpg
from fastapi import Request
import hashlib
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from fastapi.encoders import jsonable_encoder

app = FastAPI()


SHARED_PATH = "/shared_data"
VOCAL_STEMS_PATH = os.path.join(SHARED_PATH, "vocal_stems")
os.makedirs(SHARED_PATH, exist_ok=True)
os.makedirs(VOCAL_STEMS_PATH, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(
        dsn="postgresql://postgres:supersecret@db:5432/clanker"
    )
    yield
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for all origins (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def compute_fingerprint_hash(fingerprint: str) -> str:
    return hashlib.md5(fingerprint.encode('utf-8')).hexdigest()


async def insert_song(pool, title, artist, duration, fingerprint, lyrics, classification, accuracy, stem_name, fingerprint_hash):
    
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO songs (
                title, artist, duration, fingerprint, fingerprint_hash,
                lyrics, classification, accuracy, stem_name
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (fingerprint_hash) DO NOTHING
        """, title, artist, duration, fingerprint, fingerprint_hash, lyrics, classification, accuracy, stem_name)



def save_uploaded_file(upload_file: UploadFile) -> str:
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(SHARED_PATH, filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return filename

def preprocess(file_name: str) -> str:
    
    
    ext = Path(file_name).suffix.lower()
    input_path = os.path.join(SHARED_PATH, file_name)

    if ext == ".wav":
        return file_name  # No conversion needed

    converted_filename = Path(file_name).with_suffix(".wav").name
    temp_path = input_path

    with open(temp_path, "rb") as f:
        files = {'file': (file_name, f)}
        try:
            response = requests.post("http://clanker_acousti:8004/convert", files=files)
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to Acousti /convert: {e}")

    #print("🔁 Convert response code:", response.status_code)
    #print("📝 Convert raw body:", response.text)

    if response.status_code != 200:
        raise Exception(f"Conversion failed: {response.text}")

    try:
        converted_json = response.json()
    except Exception as e:
        raise Exception(f"Failed to parse /convert response as JSON: {e}. Raw body: {response.text}")

    os.remove(temp_path)

    converted_name = converted_json.get("filename")
    if not converted_name:
        raise Exception("Missing 'filename' in convert response")

    return converted_name


def wait_for_file(path: str, timeout: int = 10):
    start = time.time()
    while not os.path.exists(path):
        if time.time() - start > timeout:
            raise TimeoutError(f"File not found within {timeout} seconds: {path}")
        time.sleep(0.2)

def run_demucs(file_name: str):
    file_path = os.path.join(SHARED_PATH, file_name)
    with open(file_path, "rb") as f:
        files = {'file': (file_name, f)}
        response = requests.post("http://clanker_demucs:8000/separate", files=files)
    if response.status_code != 200:
        raise Exception("Demucs failed")
    return response.json()

def run_whisper(file_name: str):
    response = requests.get("http://clanker_whisper:8001/transcribe", params={"stem_name": file_name})
    if response.status_code != 200:
        raise Exception("Whisper failed")
    return response.json()

def run_classifier(lyrics: str):
    response = requests.post("http://clanker_classifier:8002/classify", json={"lyrics": lyrics})
    if response.status_code != 200:
        raise Exception("Classifier failed")
    return response.json()

def run_acousti(file_name: str):
    #print("📤 Sending request to /identify with:", file_name)
    sys.stderr.flush()
    file_path = os.path.join(SHARED_PATH, file_name)
    with open(file_path, "rb") as f:
        files = {
            "file": (file_name, f),
            "filename": (None, file_name)  # This sends as form field, not a file
        }
        #print("📤 Sending request to /identify with:", file_name)
        sys.stderr.flush()
        response = requests.post("http://clanker_acousti:8004/identify", files=files)
        

    #print("🟡 Status:", response.status_code)
    #print("🟡 Response:", response.text)

    if response.status_code != 200:
        raise Exception("Acoustic fingerprinting failed")

    return response.json()

async def get_song_by_fingerprint_hash(pool, fingerprint_hash: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM songs WHERE fingerprint_hash = $1
        """, fingerprint_hash)
        return dict(row) if row else None


@app.post("/api/analyze")
async def analyze(
    request: Request,
    audio: UploadFile = File(...),
    mode: str = Form(...),
    title: str = Form(""),
    artist: str = Form(""),
    lyrics: str = Form("")
):
    raw_filename = save_uploaded_file(audio)
    file_name = preprocess(raw_filename)

    try:
        db_pool = request.app.state.db_pool
        #print("mode is here", mode)
        result = {
            "title": title,
            "artist": artist,
            "lyrics": lyrics,
            "classification": None,
            "accuracy": None,
            "fingerprint": None,
            "duration": None,
        }

        if mode == "demucs":
            run_demucs(file_name)
        elif mode == "demucs-whisper":
            run_demucs(file_name)
            wait_for_file(os.path.join(VOCAL_STEMS_PATH, file_name))
            whisper_out = run_whisper(file_name)
            result["lyrics"] = whisper_out.get("lyrics")
        elif mode == "demucs-whisper-classifier":
            sys.stderr.flush()
            acousti_out = run_acousti(file_name)

            matches = acousti_out.get("matches", [])
            print("matches", matches)
            if matches:
                result["title"] = matches[0].get("title")
                result["artist"] = matches[0].get("artist") 
            else:
                result["title"] = "Unknown"
                result["artist"] = "Unknown"

            result["fingerprint"] = acousti_out.get("fingerprint")
            result["fingerprint_hash"] = compute_fingerprint_hash(result["fingerprint"])

            result["duration"] = acousti_out.get("duration")
            
            existing = await get_song_by_fingerprint_hash(db_pool, result["fingerprint_hash"])
            if existing:
                print("✅ Found existing song in DB, skipping processing")
                
                return {
                    "success": True,
                    "result": {
                        "title":existing["title"],
                        "artist": existing["artist"],
                        "fingerprint": existing["fingerprint"],
                        "duration": existing["duration"],
                        "lyrics": existing["lyrics"],
                        "classification": existing["classification"],
                        "accuracy": existing["accuracy"],
                    },
                    "cached": True
                }
            run_demucs(file_name)
            wait_for_file(os.path.join(VOCAL_STEMS_PATH, file_name))
            whisper_out = run_whisper(file_name)
            result["lyrics"] = whisper_out.get("lyrics")
            classifier_out = run_classifier(result["lyrics"])
            result["classification"] = classifier_out.get("classification")
            result["accuracy"] = classifier_out.get("accuracy")
        elif mode == "classifier-text":
            classifier_out = run_classifier(lyrics)
            result["classification"] = classifier_out.get("classification")
            result["accuracy"] = classifier_out.get("accuracy")
        else:
            return {"success": False, "error": f"Invalid mode: {mode}"}

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