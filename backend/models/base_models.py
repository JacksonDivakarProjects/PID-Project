from pydantic import BaseModel

class Base64Request(BaseModel):
    image_base64: str
    filename: str = "image.png"

class Base64Response(BaseModel):
    filename: str
    annotated_image_base64: str
    excel_data_base64: str