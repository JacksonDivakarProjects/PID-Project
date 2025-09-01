from fastapi import File, HTTPException
import base64
from pathlib import Path

from config.settings import MODEL,client

def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 string"""
    try:
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error encoding image: {str(e)}")

def extract_text_from_image(image_base64: str, mime_type: str = "image/jpeg",component_name: str = "not available") -> str:
    """Extract text from base64 encoded image using OpenAI API"""
    try:
        print(f"""
              You are an expert P&ID reader.
                Input: image + component name.
                Output every visible label/ID on the drawing, one per line, exactly as they appear (including hyphens, spaces, suffixes).
                Do not add extra text or explanation.
              componendt name: {component_name}
                """)
        response = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"""
                 You are an expert in reading P&ID diagrams.  
Input: a cropped image of a single P&ID symbol.  

Your task:  
- Extract ONLY the tag/label that is written inside or immediately next to the given symbol.  
- The tag is typically a short code like "OP-11854", "XV-203", "LT-101" etc.  
- Ignore all other surrounding text, notes, descriptions, line numbers, or extra commentary.  
- If no tag/label is visible, return exactly: Nothing  

Output format:  
Return only the exact tag/label text (e.g., OP-11854).  
Return nothing else — no explanations, no steps, no extra text.

              componendt name: {component_name}"""},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                    },
                },
            ],
        }
    ],
    model="meta-llama/llama-4-scout-17b-16e-instruct",
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
