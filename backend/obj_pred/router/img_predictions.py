

import base64
import io
import cv2
import numpy as np
import pandas as pd

import binascii
from fastapi import FastAPI, File, UploadFile, HTTPException,APIRouter
from fastapi.responses import StreamingResponse, JSONResponse



from backend.config.settings import *
from backend.models.base_models import Base64Request, Base64Response
from backend.obj_pred.services.perform_obj_pred import perform_inference_and_nms

router = APIRouter(prefix="/img_pred", tags=["Roboflow P&ID Inference API"])

@router.post("/predict-upload-json/", response_model=Base64Response)
async def predict_upload_and_get_json(file: UploadFile = File(...)):
    """
    Accepts an image file upload and returns a JSON object containing
    Base64 encoded strings for both the annotated image and the Excel data.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image_np is None:
        raise HTTPException(status_code=400, detail="Invalid image file provided.")

    try:
        final_predictions = await perform_inference_and_nms(image_np)

        # --- Generate Excel data and encode it to Base64 ---
        if not final_predictions:
            df = pd.DataFrame(columns=['x', 'y', 'width', 'height', 'confidence', 'class', 'Component Name'])
        else:
            df = pd.DataFrame(final_predictions)
            df['Component Name'] = df['class'].map(CLASS_MAPPING)
        
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        excel_base64 = base64.b64encode(excel_buffer.read()).decode('utf-8')

        # --- Generate annotated image and encode it to Base64 ---
        for p in final_predictions:
            x1 = int(p['x'] - p['width'] / 2); y1 = int(p['y'] - p['height'] / 2)
            x2 = int(p['x'] + p['width'] / 2); y2 = int(p['y'] + p['height'] / 2)
            cv2.rectangle(image_np, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{p['class']}: {CLASS_MAPPING.get(p['class'], 'Unknown')}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(image_np, (x1, y1 - h - 10), (x1 + w, y1), (0, 0, 255), -1)
            cv2.putText(image_np, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        is_success, image_buffer_encoded = cv2.imencode(".png", image_np)
        if not is_success:
            raise HTTPException(status_code=500, detail="Could not encode image to PNG.")
        image_base64 = base64.b64encode(image_buffer_encoded.tobytes()).decode('utf-8')

        # Return the Pydantic response model
        return Base64Response(
            filename=file.filename,
            annotated_image_base64=image_base64,
            excel_data_base64=excel_base64
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {e}")


@router.post("/predict-json/", response_model=Base64Response)
async def predict_base64_and_get_json(request: Base64Request):
    """
    Accepts a Base64 encoded image and returns a JSON object containing
    Base64 encoded strings for both the annotated image and the Excel data.
    """
    # (This endpoint from the previous answer remains unchanged)
    try:
        image_bytes = base64.b64decode(request.image_base64)
    except (binascii.Error, TypeError):
        raise HTTPException(status_code=400, detail="Invalid Base64 string provided.")
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_np is None:
        raise HTTPException(status_code=400, detail="Base64 string does not represent a valid image.")
    try:
        final_predictions = await perform_inference_and_nms(image_np)
        if not final_predictions:
            df = pd.DataFrame(columns=['x', 'y', 'width', 'height', 'confidence', 'class', 'Component Name'])
        else:
            df = pd.DataFrame(final_predictions)
            df['Component Name'] = df['class'].map(CLASS_MAPPING)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        excel_base64 = base64.b64encode(excel_buffer.read()).decode('utf-8')
        for p in final_predictions:
            x1 = int(p['x'] - p['width'] / 2); y1 = int(p['y'] - p['height'] / 2)
            x2 = int(p['x'] + p['width'] / 2); y2 = int(p['y'] + p['height'] / 2)
            cv2.rectangle(image_np, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{p['class']}: {CLASS_MAPPING.get(p['class'], 'Unknown')}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(image_np, (x1, y1 - h - 10), (x1 + w, y1), (0, 0, 255), -1)
            cv2.putText(image_np, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        is_success, image_buffer_encoded = cv2.imencode(".png", image_np)
        if not is_success:
            raise HTTPException(status_code=500, detail="Could not encode image to PNG.")
        image_base64 = base64.b64encode(image_buffer_encoded.tobytes()).decode('utf-8')
        return Base64Response(
            filename=request.filename,
            annotated_image_base64=image_base64,
            excel_data_base64=excel_base64
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {e}")


@router.get("/")
def read_root():
    return {
        "message": "Welcome!",
        "endpoints": {
            "/predict-upload-json/": "Upload an image file to get a JSON response.",
            "/predict-json/": "Send a JSON payload with a Base64 image to get a JSON response."
        }
    }