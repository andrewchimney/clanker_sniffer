# acoustid-api/main.py
import os
import subprocess
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import shutil
from pathlib import Path

app = FastAPI()

# Optional: Allow frontend calls during local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_fpcalc(file_path):
    result = subprocess.run(["fpcalc", file_path], capture_output=True, text=True)

    if "FINGERPRINT=" not in result.stdout or "DURATION=" not in result.stdout:
        raise RuntimeError(f"fpcalc failed: {result.stderr}")

    fingerprint = None
    duration = None

    for line in result.stdout.splitlines():
        if line.startswith("FINGERPRINT="):
            fingerprint = line.split("=", 1)[1]
        elif line.startswith("DURATION="):
            duration = int(float(line.split("=", 1)[1]))

    if not fingerprint or not duration:
        raise RuntimeError("Missing fingerprint or duration")

    return fingerprint, duration


def lookup_acoustid(fingerprint, duration, api_key):
    url = "https://api.acoustid.org/v2/lookup"
    payload = {
        "client": api_key,
        "format": "json",
        "fingerprint": fingerprint,
        "duration": duration,
        "meta": "recordings"
    }

    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise RuntimeError(f"AcoustID error: {response.text}")

    return response.json()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/convert")
async def convert_audio(file: UploadFile = File(...)):
    print("🟦 [Acousti] converting...")
    #print("📥 Received file:", file.filename)
    input_path = f"/shared_data/tmp_{file.filename}"
    output_path = f"/shared_data/{file.filename}.wav"

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
                output_path
            ],
            check=True,
            capture_output=True,
            text=True
        )

        #print("✅ FFmpeg succeeded")
        #print("📄 FFmpeg stdout:\n", result.stdout)
        #print("⚠️ FFmpeg stderr:\n", result.stderr)

        os.remove(input_path)
        return JSONResponse({"filename": os.path.basename(output_path)})

    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg failed")
        print("📄 FFmpeg stdout:\n", e.stdout)
        print("⚠️ FFmpeg stderr:\n", e.stderr)
        return JSONResponse(
            {
                "converted": False,
                "error": "FFmpeg failed",
                "stdout": e.stdout,
                "stderr": e.stderr
            },
            status_code=500
        )


@app.post("/identify")
async def identify(file: UploadFile, filename: str = Form(...)):
    try:
        print("🟦 [Acousti] identifying...")
        audio_path = f"/shared_data/{filename}"
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        api_key = os.getenv("ACOUSTID_API_KEY")
        if not api_key:
            raise RuntimeError("Missing ACOUSTID_API_KEY env var")

        fingerprint, duration = run_fpcalc(audio_path)
        raw_result = lookup_acoustid(fingerprint, duration, api_key)

        matches = []
        for result in raw_result.get("results", []):
            for recording in result.get("recordings", []):
                title = recording.get("title", "Unknown")
                artist = "Unknown"
                if recording.get("artists"):
                    artist = recording["artists"][0].get("name", "Unknown")
                matches.append({"title": title, "artist": artist})
        #print("matches acousti", matches)
        return JSONResponse({
            "fingerprint": fingerprint,
            "duration": duration,
            "matches": matches,
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
