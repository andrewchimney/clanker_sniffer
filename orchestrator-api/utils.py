import os
import uuid
import hashlib
import shutil
from fastapi import UploadFile
from typing import Optional, Dict, Any


# Shared paths
SHARED_PATH = "/shared_data"
STEMS_PATH = os.path.join(SHARED_PATH, "stems")
RAW_PATH = os.path.join(SHARED_PATH, "raw")
PREPROCESSED_PATH = os.path.join(SHARED_PATH, "preprocessed")

# Ensure directories exist
os.makedirs(SHARED_PATH, exist_ok=True)
os.makedirs(STEMS_PATH, exist_ok=True)
os.makedirs(PREPROCESSED_PATH, exist_ok=True)
os.makedirs(RAW_PATH, exist_ok=True)

#other os
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")


def compute_fingerprint_hash(fingerprint: str) -> str:
    return hashlib.md5(fingerprint.encode("utf-8")).hexdigest()


def save_uploaded_file(upload_file: UploadFile) -> str:
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(RAW_PATH, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    return filename

def make_unique_key(stage: str, file_name: Optional[str], payload: Dict[str,Any]) -> str:
    fp_hash = payload.get("fingerprint_hash") or ""
    base = f"{stage}|{file_name or ''}|{fp_hash}"
    return hashlib.sha1(base.encode()).hexdigest()

