from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import sys
import json

app = FastAPI()

class LyricsInput(BaseModel):
    lyrics: str

@app.post("/classify")
def classify(input: LyricsInput):
    print("🟥 [Classifier] running inference...")
    lyrics = input.lyrics
    #print(f"📥 Received: {lyrics}", file=sys.stderr)

    # Simulated classification result
    classification = "AI"
    accuracy = 0.9324

    return {
        "classification": classification,
        "accuracy": accuracy
    }
