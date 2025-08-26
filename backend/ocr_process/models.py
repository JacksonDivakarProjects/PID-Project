from groq import Groq
import base64
import os

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = "backend/ocr_process/sample-p&id/sample-2.jpeg"

# Getting the base64 string
base64_image = encode_image(image_path)

client = Groq(api_key="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")

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all text from this image. Return only the extracted text without any additional formatting or explanation:"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ],
    model="meta-llama/llama-4-scout-17b-16e-instruct",
)

print(chat_completion.choices[0].message.content)