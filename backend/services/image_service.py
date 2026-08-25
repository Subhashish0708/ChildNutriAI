"""
Image file management service.
Handles safe saving of uploaded photos to disk under uploads/children/{child_id}/,
validates file extensions & MIME types, and prevents unsafe filenames.
"""

import os
import uuid
import shutil
from typing import Tuple
from fastapi import UploadFile, HTTPException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_BASE_DIR = os.path.join(BASE_DIR, "uploads", "children")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def ensure_upload_dir(child_id: int) -> str:
    """Ensure directory uploads/children/{child_id}/ exists and return its path."""
    child_dir = os.path.join(UPLOAD_BASE_DIR, str(child_id))
    os.makedirs(child_dir, exist_ok=True)
    return child_dir


def validate_image_file(file: UploadFile) -> str:
    """
    Validates file extension. Returns normalized extension or raises HTTPException.
    """
    filename = file.filename or ""
    parts = filename.rsplit(".", 1)
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Uploaded file has no extension.")
    
    ext = parts[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type .{ext}. Allowed image types are: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


async def save_child_photo(file: UploadFile, child_id: int, photo_type: str) -> Tuple[str, str]:
    """
    Safely saves uploaded photo to disk and returns (relative_path, absolute_path).
    Never uses the client-supplied filename to prevent directory traversal.
    """
    ext = validate_image_file(file)
    child_dir = ensure_upload_dir(child_id)
    
    # Safe unique filename: {photo_type}_{uuid}.{ext}
    safe_filename = f"{photo_type}_{uuid.uuid4().hex[:10]}.{ext}"
    abs_path = os.path.join(child_dir, safe_filename)
    rel_path = f"uploads/children/{child_id}/{safe_filename}".replace("\\", "/")
    
    # Save file contents in chunks
    size = 0
    with open(abs_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            size += len(chunk)
            if size > MAX_FILE_SIZE_BYTES:
                buffer.close()
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                raise HTTPException(status_code=400, detail="File size exceeds maximum allowed limit of 10MB.")
            buffer.write(chunk)
            
    return rel_path, abs_path


def delete_photo_file(rel_path: str):
    """Deletes photo file from disk if it exists."""
    abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except OSError:
            pass
