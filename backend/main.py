# main.py or app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ocr_process.router.pnid_text_ret import router as ocr_router  
from ocr_process.router.excel_text_ret import router as excel_text_ret  
from obj_pred.router.img_predictions import router as img_pred_router
from graph_builder.router.graph_creator import router as graph_creator_router

app = FastAPI(
    title="OCR Text Extraction API",
    description="API for extracting text from images using Vision AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the OCR router
app.include_router(ocr_router)
app.include_router(excel_text_ret)
app.include_router(img_pred_router)
app.include_router(graph_creator_router)

@app.get("/")
async def root():
    return {"message": "OCR Text Extraction API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)