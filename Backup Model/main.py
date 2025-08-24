import cv2

# --- Configuration: You need to change these values ---

# 1. Path to the original P&ID image you processed
IMAGE_PATH = "data/raw/images/3.jpg" # Make sure this is your image name

# 2. Path to the YOLO format text file with the detections
DETECTION_FILE_PATH = "results/stage_2/few_shot/3.txt" 

# 3. Correct 0-based Class Names List
CLASS_NAMES = [
    'Gate Valve', 'Globe Valve', 'Ball Valve', 'Check Valve', 'Pressure Instrument',
    'Control Valve', 'Tagged Gate Valve', 'Local Control Station', 'Butterfly Valve',
    'Equipment Tag', 'Diaphragm Valve', 'Plug Valve', 'Needle Valve',
    'Solenoid Valve', 'Actuated Gate Valve', 'Manual Butterfly Valve',
    'Safety Relief Valve', 'Process Line Valve', 'Level Instrument',
    'Flow Instrument', 'Inline Strainer', 'Speciality Valve',
    'Junction Box ID', 'System Interface', 'Tagged Control Valve',
    'Temperature Instrument', 'High-Pressure Valve',
    'Utility Line Valve', 'Drain Valve', 'Operator Station',
    'Tagged Ball Valve', 'Analysis Instrument'
]

# 4. Path to save the final, labeled image
OUTPUT_IMAGE_PATH = "final_labeled_image_corrected.jpg"

# --- Main Script ---

# Load the image
image = cv2.imread(IMAGE_PATH)
if image is None:
    print(f"Error: Could not load image at {IMAGE_PATH}")
else:
    height, width, _ = image.shape

    # Read the detection file
    try:
        with open(DETECTION_FILE_PATH, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                    
                class_id, x_center, y_center, box_width, box_height = [float(p) for p in parts]
                class_id = int(class_id)

                # Check if the class_id is valid
                if class_id >= len(CLASS_NAMES):
                    print(f"Warning: class_id {class_id} is out of bounds for CLASS_NAMES list.")
                    continue

                abs_x_center = x_center * width
                abs_y_center = y_center * height
                abs_width = box_width * width
                abs_height = box_height * height

                x1 = int(abs_x_center - (abs_width / 2))
                y1 = int(abs_y_center - (abs_height / 2))
                x2 = int(abs_x_center + (abs_width / 2))
                y2 = int(abs_y_center + (abs_height / 2))

                # Look up the name from the 0-based CLASS_NAMES list
                label = CLASS_NAMES[class_id]

                # Draw the rectangle
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 128, 0), 2) # Dark green
                # Put the class name label on the image
                cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 0), 2)

        # Save the final image
        cv2.imwrite(OUTPUT_IMAGE_PATH, image)
        print(f"✅ Successfully created labeled image: {OUTPUT_IMAGE_PATH}")

    except FileNotFoundError:
        print(f"Error: Detection file not found at {DETECTION_FILE_PATH}")