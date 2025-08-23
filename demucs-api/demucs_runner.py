from fastapi import FastAPI, UploadFile, File, Form
import os
from pathlib import Path
import traceback
import soundfile as sf
from fastapi.responses import JSONResponse
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-9s %(message)s",
)
logger = logging.getLogger("demucs")

app = FastAPI()
MODEL = get_model(name="htdemucs")
OUTPUT_DIR = Path("/shared_data/stems")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def separate_vocals(file_path: str, output_path: str):
    ref = AudioFile(file_path).read(streams=0, samplerate=MODEL.samplerate)
    ref = ref.unsqueeze(0)
    sources = apply_model(MODEL, ref, split=True, overlap=0.25)[0]

    for idx, name in enumerate(MODEL.sources):
        if name == "vocals":
            stem = sources[idx].squeeze(0) if sources[idx].ndim == 3 else sources[idx]
            sf.write(output_path, stem.T.cpu().numpy(), MODEL.samplerate)
            return True
    return False

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/separate")
async def separate(file_path: str = Form(...)):
    logger.info("🟦Separating Stems")
    base = os.path.basename(file_path)
    output_path = f"/shared_data/stems/{base}.wav"

    try:
        success = separate_vocals(str(file_path), output_path)
        os.remove(file_path)

        if success:
            logger.info("🟦Stems Separated Successfuly")
            return JSONResponse({"file_path": output_path})
        else:
            return {"status": "error", "message": "No vocals stem found."}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
