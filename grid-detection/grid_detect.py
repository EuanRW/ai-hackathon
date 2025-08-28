import cv2
import numpy as np
from sklearn.cluster import KMeans

def cluster_lines(coords, expected_grid_size):
    """
    Cluster line coordinates using KMeans to reduce many detected lines
    to expected_grid_size + 1 coordinates.
    """
    coords = np.array(coords).reshape(-1, 1)
    if len(coords) < expected_grid_size + 1:
        # fallback: evenly spaced lines
        return np.linspace(coords.min(), coords.max(), expected_grid_size + 1, dtype=int)
    kmeans = KMeans(n_clusters=expected_grid_size + 1, random_state=0).fit(coords)
    clustered = sorted([int(c) for c in kmeans.cluster_centers_])
    return clustered


def extract_crossword_array(image_path, expected_grid_size=None, debug=False):
    """
    Detect crossword grid in image and return numpy array:
    0 = answer cell, 1 = black/non-answer cell.
    Uses Hough lines + clustering for robust detection.
    """
    # Load and preprocess
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150, apertureSize=3)

    # Detect lines
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100,
                            minLineLength=30, maxLineGap=5)
    if lines is None:
        raise ValueError("No grid lines detected")

    vertical_coords = []
    horizontal_coords = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(x1 - x2) < 10:  # vertical
            vertical_coords.append(x1)
        elif abs(y1 - y2) < 10:  # horizontal
            horizontal_coords.append(y1)

    if not vertical_coords or not horizontal_coords:
        raise ValueError("Not enough lines detected for grid")

    # Estimate grid size if not provided
    if expected_grid_size is None:
        # rough estimate: min number of vertical/horizontal lines - 1
        expected_grid_size = min(len(set(vertical_coords)) - 1,
                                 len(set(horizontal_coords)) - 1)
        if expected_grid_size < 3:
            expected_grid_size = 15  # fallback default

    # Cluster line coordinates
    v_coords = cluster_lines(vertical_coords, expected_grid_size)
    h_coords = cluster_lines(horizontal_coords, expected_grid_size)

    crossword_array = np.zeros((expected_grid_size, expected_grid_size), dtype=int)

    # Slice cells between lines and classify
    for i in range(expected_grid_size):
        for j in range(expected_grid_size):
            y1, y2 = h_coords[i], h_coords[i + 1]
            x1, x2 = v_coords[j], v_coords[j + 1]
            cell = gray[y1:y2, x1:x2]
            mean_val = np.mean(cell)
            crossword_array[i, j] = 1 if mean_val < 127 else 0

    if debug:
        print("Detected grid size:", expected_grid_size)
        print(crossword_array)

    return crossword_array


def print_crossword_grid(arr):
    """Pretty-print the crossword using . for answer cells and # for black cells."""
    for row in arr:
        print("".join('#' if val == 1 else '.' for val in row))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python grid_detect.py <image_path>")
        exit(1)

    img_path = sys.argv[1]
    grid = extract_crossword_array(img_path, debug=True)
    print_crossword_grid(grid)
