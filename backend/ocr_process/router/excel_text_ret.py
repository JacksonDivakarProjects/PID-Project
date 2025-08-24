from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from PIL import Image
import io
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

router = APIRouter(prefix="/excel_ocr", tags=["EXCEL_OCR"])

# Reuse existing functions from your services
from backend.ocr_process.services.pnid_img_text_process import (
    encode_image_to_base64,
    extract_text_from_image,
    get_mime_type
)

def crop_image_region(image: Image.Image, x: float, y: float, width: float, height: float) -> Image.Image:
    """
    Crop a specific region from an image based on bounding box coordinates
    
    Args:
        image: PIL Image object
        x, y: Center coordinates of the bounding box
        width, height: Dimensions of the bounding box
        
    Returns:
        Cropped PIL Image
    """
    # Convert center coordinates to top-left coordinates
    left = int(x - width / 2)
    top = int(y - height / 2)
    right = int(x + width / 2)
    bottom = int(y + height / 2)
    
    # Ensure coordinates are within image bounds
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)
    
    # Validate crop dimensions
    if right <= left or bottom <= top:
        raise ValueError(f"Invalid crop dimensions: left={left}, top={top}, right={right}, bottom={bottom}")
    
    # Crop the image
    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image

def process_excel_regions(df: pd.DataFrame, source_image: Image.Image) -> pd.DataFrame:
    """
    Process Excel DataFrame with bounding boxes and extract text from each region
    
    Args:
        df: DataFrame with columns x, y, width, height
        source_image: PIL Image object
        
    Returns:
        Updated DataFrame with extracted_text column
    """
    # Initialize extracted_text column
    df['extracted_text'] = ''
    df['ocr_status'] = ''
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            # Extract coordinates
            x = float(row['x'])
            y = float(row['y'])
            width = float(row['width'])
            height = float(row['height'])
            
            # Skip if dimensions are too small (likely noise)
            if width < 5 or height < 5:
                df.at[idx, 'extracted_text'] = 'REGION_TOO_SMALL'
                df.at[idx, 'ocr_status'] = 'SKIPPED'
                continue
            
            # Crop image region
            cropped_image = crop_image_region(source_image, x, y, width, height)
            
            # Save cropped image to temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_crop:
                cropped_image.save(temp_crop.name, format='PNG')
                temp_crop_path = temp_crop.name
            
            try:
                # Use existing functions to process the cropped image
                mime_type = 'image/png'
                image_base64 = encode_image_to_base64(temp_crop_path)
                extracted_text = extract_text_from_image(image_base64, mime_type)
                
                # Clean extracted text
                extracted_text = extracted_text.strip()
                if not extracted_text or extracted_text.lower() in ['', 'no text', 'no_text']:
                    extracted_text = 'NO_TEXT_FOUND'
                
                df.at[idx, 'extracted_text'] = extracted_text
                df.at[idx, 'ocr_status'] = 'SUCCESS'
                
            finally:
                # Clean up temporary crop file
                if os.path.exists(temp_crop_path):
                    os.unlink(temp_crop_path)
                    
        except Exception as e:
            df.at[idx, 'extracted_text'] = f'ERROR: {str(e)[:100]}'  # Limit error message length
            df.at[idx, 'ocr_status'] = 'FAILED'
    
    return df

# Add to your existing router
@router.post("/process-excel-with-image")
async def process_excel_with_image(
    excel_file: UploadFile = File(..., description="Excel file with bounding box data (columns: x, y, width, height)"),
    image_file: UploadFile = File(..., description="Source image for OCR processing")
):
    """
    Process Excel file with bounding boxes and extract text from corresponding image regions
    
    Args:
        excel_file: Excel file with columns: x, y, width, height (and optionally others)
        image_file: Source image file (jpg, jpeg, png, gif, bmp, webp)
        
    Returns:
        Updated Excel file with extracted_text and ocr_status columns
    """
    
    # Validate Excel file type
    if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Excel file must be .xlsx or .xls format"
        )
    
    # Validate image file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_extension = Path(image_file.filename).suffix.lower()
    
    if image_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported image type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    temp_excel_path = None
    temp_image_path = None
    
    try:
        # Save uploaded Excel file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_excel:
            excel_content = await excel_file.read()
            temp_excel.write(excel_content)
            temp_excel_path = temp_excel.name
        
        # Save uploaded image file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=image_extension) as temp_image:
            image_content = await image_file.read()
            temp_image.write(image_content)
            temp_image_path = temp_image.name
        
        # Load Excel data
        try:
            df = pd.read_excel(temp_excel_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading Excel file: {str(e)}")
        
        # Validate required columns
        required_columns = ['x', 'y', 'width', 'height']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Excel file missing required columns: {missing_columns}. Found columns: {list(df.columns)}"
            )
        
        # Load source image
        try:
            source_image = Image.open(temp_image_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error loading image: {str(e)}")
        
        # Process Excel data with OCR
        updated_df = process_excel_regions(df, source_image)
        
        # Create output Excel file in memory
        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            updated_df.to_excel(writer, sheet_name='OCR_Results', index=False)
        
        output_buffer.seek(0)
        
        # Generate output filename
        original_name = Path(excel_file.filename).stem
        output_filename = f"{original_name}_with_ocr_results.xlsx"
        
        # Clean up temporary files
        if temp_excel_path and os.path.exists(temp_excel_path):
            os.unlink(temp_excel_path)
        if temp_image_path and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
        
        # Return processed Excel file
        return StreamingResponse(
            io.BytesIO(output_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temporary files on error
        if temp_excel_path and os.path.exists(temp_excel_path):
            os.unlink(temp_excel_path)
        if temp_image_path and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during processing: {str(e)}"
        )

@router.get("/excel-processing-info")
async def get_excel_processing_info() -> Dict[str, Any]:
    """Get information about Excel processing requirements"""
    return {
        "required_excel_columns": ["x", "y", "width", "height"],
        "supported_image_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "coordinate_system": "center_based",
        "coordinate_description": {
            "x": "Center X coordinate of bounding box",
            "y": "Center Y coordinate of bounding box", 
            "width": "Width of bounding box",
            "height": "Height of bounding box"
        },
        "output_columns": ["extracted_text", "ocr_status"],
        "usage": "Upload Excel file with bounding box data and corresponding source image"
    }