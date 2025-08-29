# main.py

import os
import base64
import io
import cv2
import numpy as np
import pandas as pd
import torch
import zipfile
import binascii
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
from pydantic import BaseModel
from sahi.slicing import slice_image
from inference_sdk import InferenceHTTPClient
from torchvision.ops import nms
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Roboflow P&ID Inference API")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# --- 1. CONFIGURATION ---

# Pydantic models for structured JSON request and response
class Base64Request(BaseModel):
    image_base64: str
    filename: str = "image.png"

class Base64Response(BaseModel):
    filename: str
    annotated_image_base64: str
    excel_data_base64: str

# Initialize FastAPI app

# Your Roboflow API client

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key='ezRD6iXIbVeZMHDl6T28'
)

# Mapping dictionary
CLASS_MAPPING = {
    '1': 'Gate Valve', '2': 'Globe Valve', '3': 'Ball Valve', '4': 'Check Valve', '5': 'Pressure Instrument',
    '6': 'Control Valve', '7': 'Tagged Gate Valve', '8': 'Local Control Station', '9': 'Butterfly Valve',
    '10': 'Equipment Tag', '11': 'Diaphragm Valve', '12': 'Plug Valve', '13': 'Needle Valve',
    '14': 'Solenoid Valve', '15': 'Actuated Gate Valve', '16': 'Manual Butterfly Valve',
    '17': 'Safety Relief Valve', '18': 'Process Line Valve', '19': 'Level Instrument',
    '20': 'Flow Instrument', '21': 'Inline Strainer', '22': 'Speciality Valve',
    '23': 'Junction Box ID', '24': 'System Interface', '25': 'Tagged Control Valve',
    '26': 'Temperature Instrument', '27': 'High-Pressure Valve',
    '28': 'Utility Line Valve', '29': 'Drain Valve', '30': 'Operator Station',
    '31': 'Tagged Ball Valve', '32': 'Analysis Instrument'
}

# --- 2. CORE LOGIC ---

async def perform_inference_and_nms(image_np: np.ndarray):
    """Performs SAHI slicing, Roboflow inference, and NMS on a given image."""
    sliced_image_list = slice_image(image=image_np, slice_height=1024, slice_width=1024, overlap_height_ratio=0.2, overlap_width_ratio=0.2)
    
    all_predictions = []
    for sliced_image in sliced_image_list:
        slice_data = sliced_image['image']
        y_start, x_start = sliced_image['starting_pixel']

        slice_pil = Image.fromarray(cv2.cvtColor(slice_data, cv2.COLOR_BGR2RGB))
        buffer = io.BytesIO()
        slice_pil.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        result = CLIENT.infer(img_base64, model_id="project-pid-f2quh/1")

        for prediction in result['predictions']:
            prediction['x'] += x_start
            prediction['y'] += y_start
            all_predictions.append(prediction)

    boxes, scores, original_indices = [], [], []
    for i, p in enumerate(all_predictions):
        boxes.append([p['x'] - p['width'] / 2, p['y'] - p['height'] / 2, p['x'] + p['width'] / 2, p['y'] + p['height'] / 2])
        scores.append(p['confidence'])
        original_indices.append(i)

    if boxes:
        boxes_tensor = torch.tensor(boxes, dtype=torch.float32)
        scores_tensor = torch.tensor(scores, dtype=torch.float32)
        keep_indices_tensor = nms(boxes_tensor, scores_tensor, iou_threshold=0.45)
        return [all_predictions[original_indices[i]] for i in keep_indices_tensor]
    return []

# --- 3. API ENDPOINTS ---

@app.post("/predict-upload-json/", response_model=Base64Response)
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

@app.post("/predict-json/", response_model=Base64Response)
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

@app.get("/")
def read_root():
    return {
        "message": "Welcome!",
        "endpoints": {
            "/predict-upload-json/": "Upload an image file to get a JSON response.",
            "/predict-json/": "Send a JSON payload with a Base64 image to get a JSON response."
        }
    }