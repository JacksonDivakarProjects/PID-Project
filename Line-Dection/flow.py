import cv2
import numpy as np
import pandas as pd
import networkx as nx
import json
from shapely.geometry import Point, box

# ==================================================
# Step 1: Detect Lines (pipes) using Hough Transform
# ==================================================
def detect_lines(image_path, use_morph=True):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    edges = cv2.Canny(img, 50, 150, apertureSize=3)

    if use_morph:
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100,
                            minLineLength=50, maxLineGap=10)

    segments = []
    if lines is not None:
        for line in lines:
            x1,y1,x2,y2 = line[0]
            segments.append((x1,y1,x2,y2))
    return segments


# ==================================================
# Step 2: Load Components from Excel
# ==================================================
def load_components(excel_path):
    df = pd.read_excel(excel_path)
    components = []
    for _, row in df.iterrows():
        x, y, w, h = row['x'], row['y'], row['width'], row['height']
        bbox = [x, y, x+w, y+h]  # convert xywh → xyxy
        components.append({
            "id": str(row['detection_id']),
            "label": str(row['Component Name']),
            "class": str(row['class']),
            "bbox": bbox
        })
    return components


# ==================================================
# Step 3: Build Graph from Components + Segments
# ==================================================
def build_graph(components, segments, attach_tol=15):
    G = nx.Graph()
    comp_boxes = {}

    # Add component nodes
    for c in components:
        G.add_node(c['id'], type=c['class'], label=c['label'], bbox=c['bbox'])
        comp_boxes[c['id']] = box(*c['bbox'])

    # Add line-based edges
    for (x1,y1,x2,y2) in segments:
        p1, p2 = Point(x1,y1), Point(x2,y2)
        c1 = c2 = None
        for cid, cb in comp_boxes.items():
            if cb.buffer(attach_tol).contains(p1): c1 = cid
            if cb.buffer(attach_tol).contains(p2): c2 = cid
        if c1 and c2 and c1 != c2:
            G.add_edge(c1, c2, length=np.hypot(x2-x1, y2-y1))
    return G


# ==================================================
# Step 4: Export Graph as JSON
# ==================================================
def export_graph_json(G, output_path="pid_graph.json"):
    nodes = []
    edges = []
    for n, data in G.nodes(data=True):
        nodes.append({
            "id": n,
            "label": data.get("label"),
            "type": data.get("type"),
            "bbox": [float(v) for v in data.get("bbox", [])]
        })
    for u,v,data in G.edges(data=True):
        edges.append({
            "from": u,
            "to": v,
            "length": float(data.get("length", 0.0))
        })

    graph_json = {"nodes": nodes, "edges": edges}
    with open(output_path, "w") as f:
        json.dump(graph_json, f, indent=2)
    print(f"[✔] Graph exported to {output_path}")


# ==================================================
# Step 5: Main Pipeline
# ==================================================
def run_pipeline(image_path, excel_path, output_json="pid_graph.json", do_morph=True):
    print("[1] Detecting lines...")
    segments = detect_lines(image_path, use_morph=do_morph)
    print(f"Detected {len(segments)} line segments.")

    print("[2] Loading components...")
    components = load_components(excel_path)
    print(f"Loaded {len(components)} components.")

    print("[3] Building connectivity graph...")
    G = build_graph(components, segments)

    print("[4] Exporting to JSON...")
    export_graph_json(G, output_json)

    return G


# ==================================================
# Run Example
# ==================================================
if __name__ == "__main__":
    # 🔹 Change these paths to your own files
    image_path = r"D:\ai-art_generator\myenv\test.jpg"
    excel_path = r"D:\ai-art_generator\myenv\predictions_with_components.xlsx"
    output_path = r"D:\p&id-project\pid_graph.json"

    run_pipeline(image_path, excel_path, output_json=output_path, do_morph=True)
