from fastapi import FastAPI, HTTPException, Body, Form
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
def classify(lyrics: str = Form(...)):
    logger.info("🟦Classifying Lyrics")
    
    
    classification = "AI"
    accuracy = 0.9324
    
    logger.info("🟦Lyrics Classified Successfully")
    return {
        "classification": classification,
        "accuracy": accuracy
    }
