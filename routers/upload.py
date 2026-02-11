from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Request
from pathlib import Path
import os
import uuid
from middleware.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("")
async def upload_file(
    request: Request,
    image: UploadFile = File(...)
):
    """Upload a file"""
    # Try to get current user but don't require it (for now)
    try:
        user = await get_current_user(request)
        print(f"[UPLOAD] Upload request from user: {user.email}")
    except:
        print(f"[UPLOAD] Upload request (no auth)")
    
    print(f"[UPLOAD] File details - Filename: {image.filename}, Content-Type: {image.content_type}")
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded"
        )
    
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}
    file_ext = Path(image.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        contents = await image.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        print(f"[SUCCESS] File saved successfully: {file_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    return {
        "message": "File uploaded successfully",
        "image": f"/{file_path.as_posix()}"
    }
