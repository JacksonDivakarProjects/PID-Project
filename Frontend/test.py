import cv2
import numpy as np
import json

# ===================================================================
# 1. CONFIGURATION
# ===================================================================
# The JSON file containing your digitized P&ID data
JSON_INPUT_PATH = 'pid_data_complete.json'

# The name of the output image file that will be created
OUTPUT_IMAGE_PATH = 'reconstructed_pid_lines_only.jpg'

# ===================================================================
# 2. MAIN RECONSTRUCTION SCRIPT
# ===================================================================
if __name__ == "__main__":
    print(f"🔄 Loading digitized data from '{JSON_INPUT_PATH}'...")
    
    # Load the data from the JSON file
    try:
        with open(JSON_INPUT_PATH, 'r') as f:
            pid_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: JSON file not found at '{JSON_INPUT_PATH}'. Please make sure the file exists.")
        exit()

    # Get image dimensions from the JSON data
    width = pid_data.get('image_width')
    height = pid_data.get('image_height')

    # Create a blank, white canvas to draw on for better visibility
    # Note: Switched to a white background (255, 255, 255) with black lines (0, 0, 0)
    reconstructed_image = np.full((height, width, 3), 255, dtype=np.uint8)
    print("🎨 Created a blank canvas for reconstruction.")

    # --- Step 1: Draw the Pipeline Segments ONLY ---
    print("✍️ Drawing pipeline segments...")
    segments = pid_data.get('segments', [])
    for segment in segments:
        # Convert the list of points into a NumPy array for drawing
        points = np.array(segment, dtype=np.int32)
        # Use cv2.polylines to draw the entire segment at once
        # Drawing lines in black for better contrast on a white background
        cv2.polylines(reconstructed_image, [points], isClosed=False, color=(0, 0, 0), thickness=2)

    # --- The sections for drawing junctions and endpoints have been removed ---

    # --- Step 2: Save the Final Reconstructed Image ---
    try:
        cv2.imwrite(OUTPUT_IMAGE_PATH, reconstructed_image)
        print(f"\n✅ Line-only reconstruction complete! Image saved to '{OUTPUT_IMAGE_PATH}'.")
    except Exception as e:
        print(f"❌ Error: Could not save the image. Reason: {e}")