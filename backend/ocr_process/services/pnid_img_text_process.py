from fastapi import File, HTTPException
import base64
from pathlib import Path

from backend.config.settings import *

def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 string"""
    try:
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error encoding image: {str(e)}")

def extract_text_from_image(image_base64: str, mime_type: str = "image/jpeg") -> str:
    """Extract text from base64 encoded image using OpenAI API"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all text from this image. Return only the extracted text without any additional formatting or explanation:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ],
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

def get_mime_type(filename: str) -> str:
    """Get MIME type based on file extension"""
    extension = Path(filename).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(extension, 'image/jpeg')
