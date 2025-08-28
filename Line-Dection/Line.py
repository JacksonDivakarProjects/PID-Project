import cv2
import numpy as np
import matplotlib.pyplot as plt

def show(img, title="Image"):
    plt.figure(figsize=(12, 8))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title(title)
    plt.axis("off")
    plt.show()

# ---------------------------
# Hough Line Detection (Probabilistic)
# ---------------------------
def detect_hough_lines(edges, vis):
    hough_segments = []
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180,
                            threshold=80,
                            minLineLength=50,
                            maxLineGap=30)   # larger gap helps with dotted lines
    if lines is not None:
        for (x1, y1, x2, y2) in lines[:, 0]:
            hough_segments.append((x1, y1, x2, y2))
            cv2.line(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)  # red
    return hough_segments

# ---------------------------
# Pixel Run Detector
# ---------------------------
def detect_pixel_runs(edges, vis):
    pixel_segments = []
    binary = (edges > 0).astype(np.uint8)

    for y in range(binary.shape[0]):
        run = []
        for x in range(binary.shape[1]):
            if binary[y, x] == 1:
                run.append((x, y))
            else:
                if len(run) > 20:  # min run length
                    pixel_segments.append((run[0][0], run[0][1],
                                           run[-1][0], run[-1][1]))
                    cv2.line(vis, run[0], run[-1], (0, 255, 0), 1)  # green
                run = []
    return pixel_segments

# ---------------------------
# Contour-based Detection (for dotted lines)
# ---------------------------
def detect_contours(edges, vis):
    contour_segments = []
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # Keep only long, thin shapes (lines/dashes)
        if max(w, h) > 20 and min(w, h) < 6:  
            if w > h:  # horizontal
                contour_segments.append((x, y + h//2, x + w, y + h//2))
                cv2.line(vis, (x, y + h//2), (x + w, y + h//2), (255, 165, 0), 2)  # orange
            else:  # vertical
                contour_segments.append((x + w//2, y, x + w//2, y + h))
                cv2.line(vis, (x + w//2, y), (x + w//2, y + h), (255, 165, 0), 2)  # orange
    return contour_segments

# ---------------------------
# MAIN PIPELINE
# ---------------------------
def detect_pipes(img_path):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Preprocess
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 50, 150, apertureSize=3)

    # Visualization copies
    vis_hough, vis_pixel, vis_contour, vis_final = img.copy(), img.copy(), img.copy(), img.copy()

    # Run all detectors
    hough_segments = detect_hough_lines(edges, vis_hough)
    pixel_segments = detect_pixel_runs(edges, vis_pixel)
    contour_segments = detect_contours(edges, vis_contour)

    # Merge results
    all_segments = hough_segments + pixel_segments + contour_segments

    # Draw final merged prediction
    for (x1, y1, x2, y2) in all_segments:
        cv2.line(vis_final, (x1, y1), (x2, y2), (255, 0, 255), 2)  # magenta

    # Show outputs
    print(f"Hough segments: {len(hough_segments)}")
    print(f"Pixel run segments: {len(pixel_segments)}")
    print(f"Contour segments: {len(contour_segments)}")
    print(f"Total merged: {len(all_segments)}")

    show(vis_hough, "Hough Transform Pipes (Red)")
    show(vis_pixel, "Pixel Run Pipes (Green)")
    show(vis_contour, "Contour Pipes (Orange)")
    show(vis_final, "Merged Prediction (Magenta)")

    return all_segments


if __name__ == "__main__":
    segments = detect_pipes("test.jpg")  # replace with your image
    print("Sample segments:", segments[:10])
