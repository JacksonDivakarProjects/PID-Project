from fastapi import APIRouter, UploadFile, File
import tempfile
from fastapi.responses import JSONResponse

from graph_builder.services.graph_create_services import load_components_from_excel,detect_pipes,build_graph_with_kdtree

router = APIRouter(prefix="/grp_creation", tags=["GRP_CREATION"])
@router.post("/generate-graph")
async def generate_graph(excel: UploadFile = File(...), image: UploadFile = File(...)):
    # Save uploaded files to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel:
        tmp_excel.write(await excel.read())
        excel_path = tmp_excel.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        tmp_img.write(await image.read())
        image_path = tmp_img.name

    # Run pipeline
    nodes, comp_centers = load_components_from_excel(excel_path)
    pipes = detect_pipes(image_path)
    edges = build_graph_with_kdtree(pipes, comp_centers)

    graph = {"nodes": nodes, "edges": edges}
    return JSONResponse(content=graph)