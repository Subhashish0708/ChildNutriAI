"""Photo upload router."""
from __future__ import annotations

import io
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.deps import get_current_user
from backend.app.models import Photo, User

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

_FORMAT_TO_EXT = {"JPEG": ".jpg", "PNG": ".png"}


def _detect_image_format(content: bytes) -> str | None:
    """Return 'JPEG' or 'PNG' using Pillow — replaces removed imghdr module."""
    try:
        with Image.open(io.BytesIO(content)) as img:
            return img.format  # 'JPEG' | 'PNG' | None
    except Exception:
        return None


@router.post("/photo", status_code=201)
async def upload_photo(
    photo_type: str = "full_body",
    delete_after_analysis: bool = True,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPEG and PNG photos are allowed.")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, f"Photo too large. Max size is {settings.MAX_UPLOAD_SIZE_MB} MB.")

    detected = _detect_image_format(content)
    if detected not in {"JPEG", "PNG"}:
        raise HTTPException(400, "The uploaded file does not look like a valid JPEG or PNG photo.")

    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    ext = _FORMAT_TO_EXT[detected]
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(upload_dir, filename)

    with open(path, "wb") as out:
        out.write(content)

    width = height = None
    try:
        with Image.open(path) as img:
            width, height = img.size
    except Exception:
        pass

    photo = Photo(
        # Pending-upload sentinel. Existing local SQLite databases may have
        # created this field as NOT NULL before Alembic migrations existed.
        assessment_id=0,
        file_path=path,
        photo_type=photo_type,
        deleted=delete_after_analysis,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return {
        "id": photo.id,
        "photo_type": photo.photo_type,
        "delete_after_analysis": delete_after_analysis,
        "quality": {
            "status": "accepted",
            "width": width,
            "height": height,
            "message": "Photo stored for advisory screening. Measurements remain the main decision source.",
        },
    }
