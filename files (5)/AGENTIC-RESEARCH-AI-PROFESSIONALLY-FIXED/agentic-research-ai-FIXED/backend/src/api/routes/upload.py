"""
File Upload API Routes
"""
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from typing import Optional
import pandas as pd
from src.auth.service import get_current_user

upload_router = APIRouter(prefix="/upload", tags=["files"])


@upload_router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    user = Depends(get_current_user),
):
    """Upload and process file."""
    
    # Validate file type
    allowed_types = ["text/csv", "application/vnd.ms-excel", "application/json"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, "File type not supported")
    
    # Validate file size (50MB max)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 50MB)")
    
    # Save file
    file_path = f"/tmp/{file.filename}"
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    # Profile file
    if file.content_type == "text/csv":
        df = pd.read_csv(file_path, nrows=1000)
        
        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "column_types": df.dtypes.astype(str).to_dict(),
            "sample": df.head(5).to_dict('records'),
        }
    else:
        profile = {}
    
    return {
        "file_id": "file-" + file.filename,
        "filename": file.filename,
        "size_mb": round(len(contents) / (1024 * 1024), 2),
        "profile": profile,
    }


# =================================================================
