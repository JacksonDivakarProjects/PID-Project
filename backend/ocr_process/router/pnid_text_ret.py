from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

import os
from typing import Dict, Any
import tempfile
from pathlib import Path


from backend.ocr_process.services.pnid_img_text_process import (
    encode_image_to_base64,
    extract_text_from_image,
    get_mime_type
)

from backend.config.settings import *


# Initialize router


router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    """
    Extract text from uploaded image file
    
    Args:
        file: Uploaded image file (jpg, jpeg, png, gif, bmp, webp)
        
    Returns:
        JSON response with extracted text
    """
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create temporary file to save uploaded image
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Read and save uploaded file
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        # Get MIME type
        mime_type = get_mime_type(file.filename)
        
        # Encode image to base64
        image_base64 = encode_image_to_base64(temp_file_path)
        
        # Extract text from image
        extracted_text = extract_text_from_image(image_base64, mime_type)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        # Return JSON response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "filename": file.filename,
                "extracted_text": extracted_text,
                "file_size": len(contents),
                "mime_type": mime_type
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "OCR Text Extraction",
        "model": MODEL
    }