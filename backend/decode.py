# decode_response.py

import json
import base64
import os

def decode_api_response(json_file_path="response.json"):
    """
    Reads a JSON file from the API, decodes the Base64 data for the
    image and Excel file, and saves them to disk.
    """
    # --- 1. Load the JSON response from the file ---
    try:
        with open(json_file_path, "r") as f:
            data = json.load(f)
        print(f"Successfully loaded data from '{json_file_path}'.")
    except FileNotFoundError:
        print(f"Error: The file '{json_file_path}' was not found. Please make sure it's in the same directory.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{json_file_path}' is not a valid JSON file.")
        return

    # --- 2. Extract the data from the JSON object ---
    try:
        original_filename = data["filename"]
        image_b64 = data["annotated_image_base64"]
        excel_b64 = data["excel_data_base64"]
    except KeyError as e:
        print(f"Error: The JSON file is missing the expected key: {e}.")
        return

    # Get the base name of the file without its original extension
    file_base_name = os.path.splitext(original_filename)[0]

    # --- 3. Decode the image and save it as a .png file ---
    try:
        image_bytes = base64.b64decode(image_b64)
        image_output_path = f"annotated_{file_base_name}.png"
        with open(image_output_path, "wb") as f:
            f.write(image_bytes)
        print(f"✅ Saved annotated image to: {image_output_path}")
    except (TypeError, base64.binascii.Error):
        print("Error: The Base64 string for the image is invalid or corrupted.")
        return


    # --- 4. Decode the Excel data and save it as a .xlsx file ---
    try:
        excel_bytes = base64.b64decode(excel_b64)
        excel_output_path = f"predictions_{file_base_name}.xlsx"
        with open(excel_output_path, "wb") as f:
            f.write(excel_bytes)
        print(f"✅ Saved Excel data to: {excel_output_path}")
    except (TypeError, base64.binascii.Error):
        print("Error: The Base64 string for the Excel data is invalid or corrupted.")
        return


if __name__ == "__main__":
    # Assuming your response from the API is saved as 'response.json'
    decode_api_response("response.json")