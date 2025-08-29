import cv2
import pandas as pd
import numpy as np
import uuid
# import json
from scipy.spatial import KDTree

def load_components_from_excel(excel_path):
    df = pd.read_excel(excel_path)
    nodes = []
    comp_centers = []

    for _, row in df.iterrows():
        x, y, w, h = row["x"], row["y"], row["width"], row["height"]
        bbox = [x, y, x + w, y + h]

        node_id = str(uuid.uuid4())
        node = {
            "id": node_id,
            "label": row["Component Name"],
            "type": str(row["class_id"]),
            "bbox": bbox,
            "component_id": str(row["extracted_text"])
        }
        nodes.append(node)

        # Store center for KDTree lookup
        center = ((x + x + w) / 2, (y + y + h) / 2)
        comp_centers.append((center, node_id))

    return nodes, comp_centers


# ---------------------------
# 2. Detect Pipes (Hough Lines)
# ---------------------------
def detect_pipes(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80,
                            minLineLength=40, maxLineGap=15)

    pipes = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            pipes.append(((x1, y1), (x2, y2)))
    return pipes


# ---------------------------
# 3. Build Graph Using KDTree
# ---------------------------
def build_graph_with_kdtree(pipes, comp_centers):
    centers = np.array([c[0] for c in comp_centers])
    ids = [c[1] for c in comp_centers]
    tree = KDTree(centers)

    edges = []

    for (p1, p2) in pipes:
        _, idx1 = tree.query(p1)
        _, idx2 = tree.query(p2)

        comp1 = ids[idx1]
        comp2 = ids[idx2]

        if comp1 != comp2:
            length = np.linalg.norm(np.array(p1) - np.array(p2))
            edge = {
                "from": comp1,
                "to": comp2,
                "length": float(length)
            }
            if not any(((e["from"] == edge["from"] and e["to"] == edge["to"]) or
                        (e["from"] == edge["to"] and e["to"] == edge["from"]))
                       for e in edges):
                edges.append(edge)

    return edges