from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import sys
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-9s %(message)s",
)
logger = logging.getLogger("classify")


app = FastAPI()

class LyricsInput(BaseModel):
    lyrics: str
    
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/classify")
def classify(input: LyricsInput):
    logger.info("🟦Classifying Lyrics🟦")
    lyrics = input.lyrics
    #print(f"📥 Received: {lyrics}", file=sys.stderr)

    # Simulated classification result
    classification = "AI"
    accuracy = 0.9324
    
    logger.info("🟦Lyrics Classified Successfully🟦")
    return {
        "classification": classification,
        "accuracy": accuracy
    }
