import os
import time
import requests
import sys
from pathlib import Path


SHARED_PATH = "/shared_data"
VOCAL_STEMS_PATH = os.path.join(SHARED_PATH, "vocal_stems")


def run_demucs(file_name: str):
    file_path = os.path.join(SHARED_PATH, file_name)
    with open(file_path, "rb") as f:
        files = {'file': (file_name, f)}
        response = requests.post("http://clanker_demucs:8000/separate", files=files)
    if response.status_code != 200:
        raise Exception("Demucs failed")
    return response.json()


def run_whisper(file_name: str):
    response = requests.get("http://clanker_whisper:8000/transcribe", params={"stem_name": file_name})
    if response.status_code != 200:
        raise Exception("Whisper failed")
    return response.json()


def run_classifier(lyrics: str):
    response = requests.post("http://clanker_classifier:8000/classify", json={"lyrics": lyrics})
    if response.status_code != 200:
        raise Exception("Classifier failed")
    return response.json()


def run_acousti(file_name: str):
    file_path = os.path.join(SHARED_PATH, file_name)
    with open(file_path, "rb") as f:
        files = {
            "file": (file_name, f),
            "filename": (None, file_name)
        }
        response = requests.post("http://clanker_acousti:8000/identify", files=files)

    if response.status_code != 200:
        raise Exception("Acoustic fingerprinting failed")

    return response.json()


def wait_for_file(path: str, timeout: int = 10):
    start = time.time()
    while not os.path.exists(path):
        if time.time() - start > timeout:
            raise TimeoutError(f"File not found within {timeout} seconds: {path}")
        time.sleep(0.2)


def preprocess(file_name: str) -> str:
    ext = Path(file_name).suffix.lower()
    input_path = os.path.join(SHARED_PATH, file_name)

    if ext == ".wav":
        return file_name

    with open(input_path, "rb") as f:
        files = {'file': (file_name, f)}
        try:
            response = requests.post("http://clanker_acousti:8000/convert", files=files)
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to Acousti /convert: {e}")

    if response.status_code != 200:
        raise Exception(f"Conversion failed: {response.text}")

    try:
        converted_json = response.json()
    except Exception as e:
        raise Exception(f"Failed to parse /convert response as JSON: {e}. Raw body: {response.text}")

    os.remove(input_path)

    converted_name = converted_json.get("filename")
    if not converted_name:
        raise Exception("Missing 'filename' in convert response")

    return converted_name
