import os
import uuid
import hashlib
import shutil
from fastapi import UploadFile

# Shared paths
SHARED_PATH = "/shared_data"
VOCAL_STEMS_PATH = os.path.join(SHARED_PATH, "vocal_stems")

# Ensure directories exist
os.makedirs(SHARED_PATH, exist_ok=True)
os.makedirs(VOCAL_STEMS_PATH, exist_ok=True)

#other os
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")


def compute_fingerprint_hash(fingerprint: str) -> str:
    return hashlib.md5(fingerprint.encode("utf-8")).hexdigest()


def save_uploaded_file(upload_file: UploadFile) -> str:
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(SHARED_PATH, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    return filename
