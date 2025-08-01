from fastapi import FastAPI, UploadFile, File
import os
from pathlib import Path
import shutil
import sys
import traceback
import soundfile as sf

from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile

app = FastAPI()
MODEL = get_model(name="htdemucs")
OUTPUT_DIR = Path("/shared_data/vocal_stems")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def separate_vocals(input_path: str, output_path: str):
    ref = AudioFile(input_path).read(streams=0, samplerate=MODEL.samplerate)
    ref = ref.unsqueeze(0)
    sources = apply_model(MODEL, ref, split=True, overlap=0.25)[0]

    for idx, name in enumerate(MODEL.sources):
        if name == "vocals":
            stem = sources[idx].squeeze(0) if sources[idx].ndim == 3 else sources[idx]
            sf.write(output_path, stem.T.cpu().numpy(), MODEL.samplerate)
            return True
    return False


@app.post("/separate")
async def separate(file: UploadFile = File(...)):
    print("🟩 [Demucs] separating stems...")
    file_name = file.filename
    input_path = Path(f"/shared_data/{file_name}")
    output_path = OUTPUT_DIR / file_name

    try:
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        #print(f"📥 Received: {input_path}", file=sys.stderr)
        #print(f"📤 Output will be: {output_path}", file=sys.stderr)

        success = separate_vocals(str(input_path), str(output_path))
        os.remove(input_path)

        if success:
            return {"status": "ok", "message": f"Vocals saved to {output_path.name}"}
        else:
            return {"status": "error", "message": "No vocals stem found."}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
