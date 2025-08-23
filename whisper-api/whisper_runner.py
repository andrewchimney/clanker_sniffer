from fastapi import FastAPI, HTTPException, Query, Form
from faster_whisper import WhisperModel
import os
import sys
import json
import traceback
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-9s %(message)s",
)
logger = logging.getLogger("whisper")

app = FastAPI()
model = WhisperModel("base", device="cpu", compute_type="int8")

VOCAL_DIR = "/shared_data/stems"

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(file_path: str = Form(...)):
    logger.info("🟦transcribing vocals")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        segments, info = model.transcribe(file_path, beam_size=5, language="en")
        transcript = " ".join(segment.text.strip() for segment in segments)
        logger.info("🟦vocals transcribed successfully")
        return {"lyrics": transcript}
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
