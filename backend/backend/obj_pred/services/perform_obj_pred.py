import torch

import base64
import io
import cv2
import numpy as np
import pandas as pd

from backend.config.settings import CLIENT

from PIL import Image
from sahi.slicing import slice_image

from torchvision.ops import nms

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
