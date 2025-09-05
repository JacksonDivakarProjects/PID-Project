import base64
import numpy as np
import pandas as pd
import cv2
from PIL import Image
from sahi.slicing import slice_image
from inference_sdk import InferenceHTTPClient
import torch
from torchvision.ops import nms # Import nms from torchvision

# --- 1. CONFIGURATION ---
# Your Roboflow API client
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="ezRD6iXIbVeZMHDl6T28"  # REPLACE WITH YOUR ACTUAL API KEY
)

# Paths for input and output files
input_image_path = "3.jpg"
output_excel_path = "predictions_with_components.xlsx"
output_image_path = "sample_output.png"

# Create a mapping dictionary from the class numbers to component names
class_mapping = {
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

# --- 2. SAHI SLICING & INFERENCE ---
# Load the image using Pillow and convert to a NumPy array for slicing
image_pil = Image.open(input_image_path)
image_np = np.array(image_pil)

# Use SAHI to slice the image with 1024x1024 dimensions
sliced_image_list = slice_image(
    image_np,
    slice_height=1024,
    slice_width=1024,
    overlap_height_ratio=0.2,
    overlap_width_ratio=0.2,
)

# A list to store all the predictions from all slices
all_predictions = []

# Loop through each slice and send it to the Roboflow API
for sliced_image in sliced_image_list:
    slice_data = sliced_image['image']

    # Get the starting coordinates from the 'starting_pixel' key
    y_start, x_start = sliced_image['starting_pixel']

    # Encode the sliced image to base64
    slice_pil = Image.fromarray(slice_data)
    slice_pil.save("temp_slice.png")
    with open("temp_slice.png", "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    # Perform inference on the slice
    result = CLIENT.infer(img_base64, model_id="project-pid-f2quh/1")

    # Adjust and store the predictions
    for prediction in result['predictions']:
        prediction['x'] += y_start
        prediction['y'] += x_start
        all_predictions.append(prediction)

# --- 3. APPLY NON-MAXIMUM SUPPRESSION (NMS) ---

# Convert predictions to a format suitable for NMS
# torchvision.ops.nms expects boxes in [x1, y1, x2, y2] format and scores
boxes = []
scores = []
# Store original prediction indices to retrieve full prediction info after NMS
original_indices = []

for i, p in enumerate(all_predictions):
    x_center, y_center, width, height, confidence = p['x'], p['y'], p['width'], p['height'], p['confidence']
    x1 = x_center - width / 2
    y1 = y_center - height / 2
    x2 = x_center + width / 2
    y2 = y_center + height / 2
    boxes.append([x1, y1, x2, y2])
    scores.append(confidence)
    original_indices.append(i)


if boxes:
    boxes_tensor = torch.tensor(boxes, dtype=torch.float32)
    scores_tensor = torch.tensor(scores, dtype=torch.float32)

    # Apply NMS
    # torchvision.ops.nms(boxes, scores, iou_threshold)
    keep_indices_tensor = nms(boxes_tensor, scores_tensor, iou_threshold=0.45)

    # Filter the original predictions based on NMS output
    # Use the original_indices to map back to the full prediction dictionaries
    final_predictions = [all_predictions[original_indices[i]] for i in keep_indices_tensor]
else:
    final_predictions = []

# --- 4. EXCEL FILE GENERATION ---

# Create a DataFrame from the final predictions
df = pd.DataFrame(final_predictions)

# Create the new 'Component Name' column by mapping the 'class' column
df['Component Name'] = df['class'].map(class_mapping)

# Save the DataFrame to an Excel file
output_excel_path = "predictions_with_components.xlsx"
df.to_excel(output_excel_path, index=False)
print(f"DataFrame with mapped component names successfully saved to {output_excel_path}.")

# --- 5. IMAGE VISUALIZATION ---

# Load the original image using OpenCV
image = cv2.imread(input_image_path)

if image is None:
    print(f"Error: Could not load image from {input_image_path}")
else:
    # Iterate through each row in the DataFrame
    for index, row in df.iterrows():
        # Get coordinates from the DataFrame
        x_center, y_center = row['x'], row['y']
        width, height = row['width'], row['height']
        class_id = row['class'] # Use 'class' which is string from Roboflow API

        # Convert center coordinates to top-left corner coordinates
        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        x2 = int(x_center + width / 2)
        y2 = int(y_center + height / 2)

        # Draw the bounding box (rectangle) on the image
        color = (0, 255, 0)  # Green color in BGR format
        thickness = 2
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)

        # Get the component name from the mapping dictionary
        component_name = class_mapping.get(class_id, "Unknown")
        label = f"{class_id}: {component_name}"

        # Put the class number and component name text on the image
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        text_color = (0, 0, 255)  # Red color for text

        cv2.putText(image, label, (x1, y1 - 10), font, font_scale, text_color, font_thickness)

    # Save the output image with bounding boxes
    cv2.imwrite(output_image_path, image)

    print(f"Image with bounding boxes saved to {output_image_path}")