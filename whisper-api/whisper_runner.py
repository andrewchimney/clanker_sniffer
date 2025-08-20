from fastapi import FastAPI, HTTPException, Query
from faster_whisper import WhisperModel
import os
import sys
import json
import traceback

app = FastAPI()
model = WhisperModel("base", device="cpu", compute_type="int8")

VOCAL_DIR = "/shared_data/vocal_stems"

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/transcribe")
def transcribe(stem_name: str = Query(..., description="Filename of stem to transcribe")):
    print("🟨 [Whisper] transcribing vocals...")
    input_path = os.path.join(VOCAL_DIR, stem_name)
    #print(f"📥 Received: {input_path}", file=sys.stderr)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        segments, info = model.transcribe(input_path, beam_size=5)
        transcript = " ".join(segment.text.strip() for segment in segments)

        #print(f"📝 Transcription: {transcript}", file=sys.stderr)
        return {"lyrics": transcript}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
