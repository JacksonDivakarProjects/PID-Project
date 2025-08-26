from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from PIL import Image
import io
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
import zipfile
from datetime import datetime
import uuid

router = APIRouter(prefix="/excel_ocr", tags=["EXCEL_OCR"])

# Reuse existing functions from your services
from backend.ocr_process.services.pnid_img_text_process import (
    encode_image_to_base64,
    extract_text_from_image,
    get_mime_type
)

def create_crops_directory(base_name: str) -> str:
    """
    Create a directory for storing cropped images
    
    Args:
        base_name: Base name for the directory
        
    Returns:
        Path to the created directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    crops_dir = f"cropped_images/{base_name}_{timestamp}_{unique_id}"
    
    os.makedirs(crops_dir, exist_ok=True)
    return crops_dir

def calculate_intelligent_padding(width: float, height: float, image_width: int, image_height: int) -> Dict[str, float]:
    """
    Calculate intelligent padding based on component size and image dimensions
    
    Args:
        width, height: Original bounding box dimensions
        image_width, image_height: Source image dimensions
        
    Returns:
        Dictionary with padding values for each direction
    """
    # Base padding as percentage of component size
    base_padding_ratio = 0.8  # 80% of component size as base padding
    
    # Calculate base padding
    base_padding_x = width * base_padding_ratio
    base_padding_y = height * base_padding_ratio
    
    # Size-based adjustments
    component_area = width * height
    
    # For very small components (likely symbols), increase padding more
    if component_area < 400:  # Small components
        size_multiplier = 2.0
    elif component_area < 1000:  # Medium components
        size_multiplier = 1.5
    else:  # Large components
        size_multiplier = 1.0
    
    # Aspect ratio considerations
    aspect_ratio = max(width, height) / min(width, height)
    
    # For very wide or very tall components, adjust padding differently
    if aspect_ratio > 3:  # Very elongated components
        if width > height:  # Wide component - more vertical padding for labels
            vertical_multiplier = 2.5
            horizontal_multiplier = 1.2
        else:  # Tall component - more horizontal padding for labels
            vertical_multiplier = 1.2
            horizontal_multiplier = 2.5
    else:  # Regular aspect ratio
        vertical_multiplier = 1.8  # More vertical padding for tags above/below
        horizontal_multiplier = 1.5
    
    # Apply multipliers
    padding_top = base_padding_y * size_multiplier * vertical_multiplier
    padding_bottom = base_padding_y * size_multiplier * vertical_multiplier
    padding_left = base_padding_x * size_multiplier * horizontal_multiplier
    padding_right = base_padding_x * size_multiplier * horizontal_multiplier
    
    # Additional padding for very small components
    min_padding = 25  # Minimum padding in pixels
    padding_top = max(padding_top, min_padding)
    padding_bottom = max(padding_bottom, min_padding)
    padding_left = max(padding_left, min_padding)
    padding_right = max(padding_right, min_padding)
    
    # Limit maximum padding to prevent excessive crops
    max_padding_x = min(200, image_width * 0.1)  # Max 10% of image width or 200px
    max_padding_y = min(200, image_height * 0.1)  # Max 10% of image height or 200px
    
    padding_top = min(padding_top, max_padding_y)
    padding_bottom = min(padding_bottom, max_padding_y)
    padding_left = min(padding_left, max_padding_x)
    padding_right = min(padding_right, max_padding_x)
    
    return {
        'top': padding_top,
        'bottom': padding_bottom,
        'left': padding_left,
        'right': padding_right
    }

def crop_image_region_with_intelligent_padding(image: Image.Image, x: float, y: float, 
                                             width: float, height: float, 
                                             enable_intelligent_padding: bool = True) -> tuple[Image.Image, Dict[str, Any]]:
    """
    Crop a specific region from an image with intelligent padding for label capture
    
    Args:
        image: PIL Image object
        x, y: Center coordinates of the bounding box
        width, height: Dimensions of the bounding box
        enable_intelligent_padding: Whether to apply intelligent padding
        
    Returns:
        Tuple of (Cropped PIL Image, crop_info dictionary)
    """
    original_left = int(x - width / 2)
    original_top = int(y - height / 2)
    original_right = int(x + width / 2)
    original_bottom = int(y + height / 2)
    
    if enable_intelligent_padding:
        # Calculate intelligent padding
        padding = calculate_intelligent_padding(width, height, image.width, image.height)
        
        # Apply padding
        left = int(original_left - padding['left'])
        top = int(original_top - padding['top'])
        right = int(original_right + padding['right'])
        bottom = int(original_bottom + padding['bottom'])
        
        padding_applied = padding
    else:
        # No padding - use original coordinates
        left = original_left
        top = original_top
        right = original_right
        bottom = original_bottom
        
        padding_applied = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}
    
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
    
    # Create crop info for debugging/verification
    crop_info = {
        'original_coords': {
            'left': original_left, 'top': original_top, 
            'right': original_right, 'bottom': original_bottom
        },
        'padded_coords': {
            'left': left, 'top': top, 
            'right': right, 'bottom': bottom
        },
        'padding_applied': padding_applied,
        'original_size': {'width': int(width), 'height': int(height)},
        'cropped_size': {'width': cropped_image.width, 'height': cropped_image.height},
        'expansion_factor': {
            'width': cropped_image.width / width,
            'height': cropped_image.height / height
        }
    }
    
    return cropped_image, crop_info

# Keep the old function for backward compatibility
def crop_image_region(image: Image.Image, x: float, y: float, width: float, height: float) -> Image.Image:
    """
    Crop a specific region from an image based on bounding box coordinates (backward compatibility)
    """
    cropped_image, _ = crop_image_region_with_intelligent_padding(image, x, y, width, height, False)
    return cropped_image

def save_cropped_image(cropped_image: Image.Image, crops_dir: str, row_index: int, 
                      x: float, y: float, width: float, height: float, 
                      crop_info: Dict[str, Any] = None) -> str:
    """
    Save cropped image with descriptive filename including expansion info
    
    Args:
        cropped_image: PIL Image object to save
        crops_dir: Directory to save the image
        row_index: Index of the row being processed
        x, y, width, height: Original bounding box coordinates
        crop_info: Information about the crop expansion
        
    Returns:
        Filename of the saved image
    """
    if crop_info and 'expansion_factor' in crop_info:
        exp_w = crop_info['expansion_factor']['width']
        exp_h = crop_info['expansion_factor']['height']
        filename = f"crop_{row_index:04d}_x{int(x)}_y{int(y)}_w{int(width)}_h{int(height)}_exp{exp_w:.1f}x{exp_h:.1f}.png"
    else:
        filename = f"crop_{row_index:04d}_x{int(x)}_y{int(y)}_w{int(width)}_h{int(height)}.png"
    
    filepath = os.path.join(crops_dir, filename)
    cropped_image.save(filepath, format='PNG')
    return filename

def process_excel_regions_with_crops(df: pd.DataFrame, source_image: Image.Image, 
                                   crops_dir: str, save_crops: bool = True,
                                   intelligent_padding: bool = True) -> pd.DataFrame:
    """
    Process Excel DataFrame with bounding boxes and extract text from each region
    
    Args:
        df: DataFrame with columns x, y, width, height
        source_image: PIL Image object
        crops_dir: Directory to save cropped images
        save_crops: Whether to save cropped images for verification
        intelligent_padding: Whether to apply intelligent padding for label capture
        
    Returns:
        Updated DataFrame with extracted_text, ocr_status, crop_filename, and crop_info columns
    """
    # Initialize new columns
    df['extracted_text'] = ''
    df['ocr_status'] = ''
    df['crop_filename'] = ''
    df['expansion_factor_w'] = 0.0
    df['expansion_factor_h'] = 0.0
    df['padding_applied'] = ''
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            # Extract coordinates
            x = float(row['x'])
            y = float(row['y'])
            width = float(row['width'])
            height = float(row['height'])
            component_name = str(row['Component Name'])
            
            # Skip if dimensions are too small (likely noise)
            if width < 5 or height < 5:
                df.at[idx, 'extracted_text'] = 'REGION_TOO_SMALL'
                df.at[idx, 'ocr_status'] = 'SKIPPED'
                df.at[idx, 'crop_filename'] = 'NOT_CREATED'
                continue
            
            # Crop image region with intelligent padding
            cropped_image, crop_info = crop_image_region_with_intelligent_padding(
                source_image, x, y, width, height, intelligent_padding
            )
            
            # Store expansion information
            df.at[idx, 'expansion_factor_w'] = crop_info['expansion_factor']['width']
            df.at[idx, 'expansion_factor_h'] = crop_info['expansion_factor']['height']
            df.at[idx, 'padding_applied'] = f"T:{int(crop_info['padding_applied']['top'])}, " \
                                           f"B:{int(crop_info['padding_applied']['bottom'])}, " \
                                           f"L:{int(crop_info['padding_applied']['left'])}, " \
                                           f"R:{int(crop_info['padding_applied']['right'])}"
            
            # Save cropped image for verification if enabled
            crop_filename = 'NOT_SAVED'
            if save_crops:
                crop_filename = save_cropped_image(cropped_image, crops_dir, idx, x, y, width, height, crop_info)
                df.at[idx, 'crop_filename'] = crop_filename
            
            # Save cropped image to temporary file for OCR processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_crop:
                cropped_image.save(temp_crop.name, format='PNG')
                temp_crop_path = temp_crop.name
            
            try:
                # Use existing functions to process the cropped image
                mime_type = 'image/png'
                image_base64 = encode_image_to_base64(temp_crop_path)
                extracted_text = extract_text_from_image(image_base64, mime_type,component_name)
                
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
            df.at[idx, 'crop_filename'] = 'ERROR_OCCURRED'
    
    return df

def create_zip_with_results(df: pd.DataFrame, crops_dir: str, excel_filename: str) -> io.BytesIO:
    """
    Create a ZIP file containing the Excel results and cropped images
    
    Args:
        df: Processed DataFrame
        crops_dir: Directory containing cropped images
        excel_filename: Name for the Excel file
        
    Returns:
        BytesIO object containing the ZIP file
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add Excel file
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='OCR_Results', index=False)
        
        excel_buffer.seek(0)
        zip_file.writestr(excel_filename, excel_buffer.getvalue())
        
        # Add cropped images
        if os.path.exists(crops_dir):
            for filename in os.listdir(crops_dir):
                if filename.endswith('.png'):
                    file_path = os.path.join(crops_dir, filename)
                    zip_file.write(file_path, f"cropped_images/{filename}")
        
        # Add a README file with information
        readme_content = f"""OCR Processing Results
========================

This ZIP file contains:
1. {excel_filename} - Excel file with OCR results
2. cropped_images/ - Directory with all cropped image regions

Excel File Columns:
- Original columns from your input file
- extracted_text: Text extracted from each region using OCR
- ocr_status: Status of OCR processing (SUCCESS, FAILED, SKIPPED)
- crop_filename: Name of the corresponding cropped image file

Cropped Image Naming Convention:
crop_XXXX_xNNN_yNNN_wNNN_hNNN.png
- XXXX: Row index (0-padded)
- xNNN, yNNN: Center coordinates
- wNNN, hNNN: Width and height

Processing Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Regions Processed: {len(df)}
Successful OCR: {len(df[df['ocr_status'] == 'SUCCESS'])}
Failed OCR: {len(df[df['ocr_status'] == 'FAILED'])}
Skipped (too small): {len(df[df['ocr_status'] == 'SKIPPED'])}
"""
        zip_file.writestr("README.txt", readme_content)
    
    zip_buffer.seek(0)
    return zip_buffer

@router.post("/process-excel-with-image")
async def process_excel_with_image(
    excel_file: UploadFile = File(..., description="Excel file with bounding box data (columns: x, y, width, height)"),
    image_file: UploadFile = File(..., description="Source image for OCR processing"),
    save_crops: bool = True,
    intelligent_padding: bool = True
):
    """
    Process Excel file with bounding boxes and extract text from corresponding image regions
    
    Args:
        excel_file: Excel file with columns: x, y, width, height (and optionally others)
        image_file: Source image file (jpg, jpeg, png, gif, bmp, webp)
        save_crops: Whether to save cropped images for verification (default: True)
        intelligent_padding: Whether to apply intelligent padding for label capture (default: True)
        
    Returns:
        ZIP file containing Excel results and cropped images (if save_crops=True)
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
    crops_dir = None
    
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
        
        # Create directory for cropped images if saving is enabled
        if save_crops:
            base_name = Path(excel_file.filename).stem
            crops_dir = create_crops_directory(base_name)
        
        # Process Excel data with OCR
        updated_df = process_excel_regions_with_crops(df, source_image, crops_dir or "", 
                                                     save_crops, intelligent_padding)
        
        # Generate output filename
        original_name = Path(excel_file.filename).stem
        padding_suffix = "_smart_padded" if intelligent_padding else "_exact"
        excel_filename = f"{original_name}{padding_suffix}_ocr_results.xlsx"
        
        if save_crops:
            # Create ZIP file with Excel results and cropped images
            zip_filename = f"{original_name}{padding_suffix}_ocr_results_with_crops.zip"
            zip_buffer = create_zip_with_results(updated_df, crops_dir, excel_filename)
            
            # Clean up temporary files
            if temp_excel_path and os.path.exists(temp_excel_path):
                os.unlink(temp_excel_path)
            if temp_image_path and os.path.exists(temp_image_path):
                os.unlink(temp_image_path)
            
            # Return ZIP file
            return StreamingResponse(
                io.BytesIO(zip_buffer.getvalue()),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
            )
        else:
            # Return only Excel file
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                updated_df.to_excel(writer, sheet_name='OCR_Results', index=False)
            
            output_buffer.seek(0)
            
            # Clean up temporary files
            if temp_excel_path and os.path.exists(temp_excel_path):
                os.unlink(temp_excel_path)
            if temp_image_path and os.path.exists(temp_image_path):
                os.unlink(temp_image_path)
            
            return StreamingResponse(
                io.BytesIO(output_buffer.getvalue()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={excel_filename}"}
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temporary files and crops directory on error
        if temp_excel_path and os.path.exists(temp_excel_path):
            os.unlink(temp_excel_path)
        if temp_image_path and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
        if crops_dir and os.path.exists(crops_dir):
            import shutil
            shutil.rmtree(crops_dir, ignore_errors=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during processing: {str(e)}"
        )(crops_dir, ignore_errors=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during processing: {str(e)}"
        )(crops_dir, ignore_errors=True)
        
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
        "output_columns": [
            "extracted_text", 
            "ocr_status", 
            "crop_filename",
            "expansion_factor_w",
            "expansion_factor_h", 
            "padding_applied"
        ],
        "intelligent_padding_features": {
            "size_based_adjustment": "Smaller components get more padding",
            "aspect_ratio_consideration": "Wide/tall components get strategic padding",
            "label_capture_optimization": "More vertical padding for component tags",
            "boundary_protection": "Prevents crops from exceeding image bounds",
            "minimum_padding": "Ensures at least 25px padding for very small components",
            "maximum_padding_limit": "Caps padding at 10% of image dimensions or 200px"
        },
        "padding_logic": {
            "small_components": "< 400px² area: 2x base padding multiplier",
            "medium_components": "400-1000px² area: 1.5x base padding multiplier", 
            "large_components": "> 1000px² area: 1x base padding multiplier",
            "elongated_components": "Aspect ratio > 3:1: Strategic directional padding",
            "base_padding": "80% of component size as starting point"
        },
        "parameters": {
            "save_crops": "Boolean - Save cropped images for verification",
            "intelligent_padding": "Boolean - Apply smart padding for label capture"
        },
        "usage_examples": {
            "default": "Both save_crops=true and intelligent_padding=true",
            "exact_crops": "intelligent_padding=false for exact bounding box crops",
            "excel_only": "save_crops=false to get only Excel results"
        }
    }

@router.post("/test-padding-preview")
async def test_padding_preview(
    excel_file: UploadFile = File(..., description="Excel file with bounding box data"),
    image_file: UploadFile = File(..., description="Source image for preview"),
    sample_size: int = 5
):
    """
    Preview intelligent padding effects on a sample of bounding boxes
    
    Args:
        excel_file: Excel file with bounding box data
        image_file: Source image file
        sample_size: Number of samples to preview (default: 5)
        
    Returns:
        JSON with padding calculation details for sample components
    """
    # Validation and file loading (similar to main function)
    if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Excel file must be .xlsx or .xls format")
    
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_extension = Path(image_file.filename).suffix.lower()
    
    if image_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported image type")
    
    temp_excel_path = None
    temp_image_path = None
    
    try:
        # Save files temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_excel:
            excel_content = await excel_file.read()
            temp_excel.write(excel_content)
            temp_excel_path = temp_excel.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=image_extension) as temp_image:
            image_content = await image_file.read()
            temp_image.write(image_content)
            temp_image_path = temp_image.name
        
        # Load data
        df = pd.read_excel(temp_excel_path)
        source_image = Image.open(temp_image_path)
        
        # Validate required columns
        required_columns = ['x', 'y', 'width', 'height']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing_columns}")
        
        # Sample data
        sample_df = df.head(sample_size)
        
        # Calculate padding for samples
        preview_results = []
        for idx, row in sample_df.iterrows():
            try:
                x, y, width, height = float(row['x']), float(row['y']), float(row['width']), float(row['height'])
                
                # Calculate padding
                padding = calculate_intelligent_padding(width, height, source_image.width, source_image.height)
                
                # Calculate expansion factors
                original_area = width * height
                padded_width = width + padding['left'] + padding['right']
                padded_height = height + padding['top'] + padding['bottom']
                padded_area = padded_width * padded_height
                
                preview_results.append({
                    "row_index": int(idx),
                    "original": {
                        "x": x, "y": y, "width": width, "height": height,
                        "area": original_area,
                        "aspect_ratio": max(width, height) / min(width, height)
                    },
                    "padding": padding,
                    "padded": {
                        "width": padded_width, "height": padded_height,
                        "area": padded_area
                    },
                    "expansion_factors": {
                        "width": padded_width / width,
                        "height": padded_height / height,
                        "area": padded_area / original_area
                    },
                    "component_classification": {
                        "size_category": "small" if original_area < 400 else "medium" if original_area < 1000 else "large",
                        "aspect_category": "elongated" if max(width, height) / min(width, height) > 3 else "regular"
                    }
                })
                
            except Exception as e:
                preview_results.append({
                    "row_index": int(idx),
                    "error": f"Error processing row: {str(e)}"
                })
        
        # Clean up
        if temp_excel_path and os.path.exists(temp_excel_path):
            os.unlink(temp_excel_path)
        if temp_image_path and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
        
        return {
            "image_dimensions": {"width": source_image.width, "height": source_image.height},
            "total_components": len(df),
            "sample_size": len(preview_results),
            "padding_preview": preview_results,
            "summary": {
                "avg_expansion_width": sum([r.get('expansion_factors', {}).get('width', 1) for r in preview_results if 'expansion_factors' in r]) / max(1, len([r for r in preview_results if 'expansion_factors' in r])),
                "avg_expansion_height": sum([r.get('expansion_factors', {}).get('height', 1) for r in preview_results if 'expansion_factors' in r]) / max(1, len([r for r in preview_results if 'expansion_factors' in r]))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if temp_excel_path and os.path.exists(temp_excel_path):
            os.unlink(temp_excel_path)
        if temp_image_path and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
        
        raise HTTPException(status_code=500, detail=f"Error in padding preview: {str(e)}")