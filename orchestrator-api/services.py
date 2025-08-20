import os
import time
import asyncio
import httpx
from pathlib import Path

# ------- config -------
SHARED_PATH = "/shared_data"
VOCAL_STEMS_PATH = os.path.join(SHARED_PATH, "vocal_stems")

ACOUSTI_URL   = os.getenv("ACOUSTI_URL",   "http://clanker_acousti:8000")
DEMUCS_URL    = os.getenv("DEMUCS_URL",    "http://clanker_demucs:8000")
WHISPER_URL   = os.getenv("WHISPER_URL",   "http://clanker_whisper:8000")
CLASSIFY_URL  = os.getenv("CLASSIFY_URL",  "http://clanker_classifier:8000")

# Timeouts (connect, read)
T_IDENTIFY   = (5.0, 120.0)
T_CONVERT    = (5.0, 120.0)
T_DEMUCS     = (5.0, 900.0)
T_WHISPER    = (5.0, 600.0)
T_CLASSIFIER = (5.0, 60.0)

# ------- global async client -------
_client = httpx.AsyncClient(timeout=None)  # we set per-request timeouts below


async def _raise(resp: httpx.Response, ctx: str):
    try:
        msg = resp.json()
    except Exception:
        msg = resp.text
    raise RuntimeError(f"{ctx} failed: HTTP {resp.status_code} - {msg}")


# ------- async helpers -------
async def run_demucs(file_name: str):
    file_path = os.path.join(SHARED_PATH, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio not found for Demucs: {file_path}")

    with open(file_path, "rb") as f:
        files = {'file': (file_name, f)}
        r = await _client.post(f"{DEMUCS_URL}/separate", files=files, timeout=T_DEMUCS)
    if r.status_code != 200:
        await _raise(r, "Demucs")
    return r.json()


async def run_whisper(file_name: str):
    r = await _client.get(f"{WHISPER_URL}/transcribe",
                          params={"stem_name": file_name},
                          timeout=T_WHISPER)
    if r.status_code != 200:
        await _raise(r, "Whisper")
    return r.json()


async def run_classifier(lyrics: str):
    r = await _client.post(f"{CLASSIFY_URL}/classify",
                           json={"lyrics": lyrics},
                           timeout=T_CLASSIFIER)
    if r.status_code != 200:
        await _raise(r, "Classifier")
    return r.json()


async def run_acousti(file_name: str):
    file_path = os.path.join(SHARED_PATH, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio not found for Acousti: {file_path}")

    with open(file_path, "rb") as f:
        files = {"file": (file_name, f), "filename": (None, file_name)}
        r = await _client.post(f"{ACOUSTI_URL}/identify", files=files, timeout=T_IDENTIFY)
    if r.status_code != 200:
        await _raise(r, "Acoustic fingerprinting")
    return r.json()


async def preprocess(file_name: str) -> str:
    input_path = os.path.join(SHARED_PATH, file_name)
    ext = Path(file_name).suffix.lower()

    if ext == ".wav":
        return file_name

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input not found for convert: {input_path}")

    with open(input_path, "rb") as f:
        files = {'file': (file_name, f)}
        try:
            r = await _client.post(f"{ACOUSTI_URL}/convert", files=files, timeout=T_CONVERT)
        except httpx.RequestError as e:
            raise RuntimeError(f"Connect to /convert failed: {e}")

    if r.status_code != 200:
        await _raise(r, "Conversion")

    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Convert returned non-JSON: {r.text}")

    converted_name = data.get("filename")
    if not converted_name:
        raise RuntimeError("Conversion response missing 'filename'")

    try:
        os.remove(input_path)
    except FileNotFoundError:
        pass

    return converted_name


# ------- sync file wait (unchanged, but use asyncio.sleep if inside async code) -------
def wait_for_file(path: str, timeout: int = 30):
    start = time.time()
    while not os.path.exists(path):
        if time.time() - start > timeout:
            raise TimeoutError(f"File not found within {timeout}s: {path}")
        time.sleep(0.2)
