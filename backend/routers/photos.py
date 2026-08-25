"""
Photo Upload and Gallery Endpoints.
Stores image files on disk in uploads/children/{child_id}/ and path metadata in SQLite.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import ChildPhoto, Child, User
from backend.schemas import PhotoResponse
from backend.services.image_service import save_child_photo, delete_photo_file
from backend.dependencies import get_current_user, check_child_access

router = APIRouter(prefix="/api/photos", tags=["Photos"])


@router.post("/upload", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    child_id: int = Form(...),
    photo_type: str = Form("front"),  # front, side, full_body
    assessment_id: Optional[int] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload child image for visual AI analysis:
    - Validates file type (jpg/jpeg/png) & file size (<= 10MB)
    - Saves file to disk under uploads/children/{child_id}/
    - Saves file path and metadata in SQLite child_photos table
    """
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child record not found.")
    check_child_access(child, current_user)

    norm_type = photo_type.lower().strip()
    if norm_type not in ["front", "side", "full_body"]:
        norm_type = "front"

    # Save to disk
    rel_path, abs_path = await save_child_photo(image, child_id, norm_type)

    # Store metadata in DB
    photo_record = ChildPhoto(
        child_id=child_id,
        assessment_id=assessment_id,
        photo_type=norm_type,
        file_path=rel_path
    )
    db.add(photo_record)
    db.commit()
    db.refresh(photo_record)
    return photo_record


@router.get("/child/{child_id}", response_model=List[PhotoResponse])
def get_child_photos(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all uploaded photos for a child."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)
    
    return db.query(ChildPhoto).filter(ChildPhoto.child_id == child_id).order_by(ChildPhoto.uploaded_at.desc()).all()


@router.delete("/{photo_id}")
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a photo record and remove the file from disk."""
    photo = db.query(ChildPhoto).filter(ChildPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    check_child_access(photo.child, current_user)

    delete_photo_file(photo.file_path)
    db.delete(photo)
    db.commit()
    return {"message": "Photo deleted successfully."}
