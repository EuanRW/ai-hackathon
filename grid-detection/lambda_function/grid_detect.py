import cv2
from pathlib import Path
import numpy as np

def find_crossword_bounding_box(image):
    """
    Finds the bounding box of the crossword puzzle in an image.
    This function operates on an already-loaded OpenCV image object.
    
    Args:
        image (np.ndarray): The input image array.
    
    Returns:
        A tuple (x, y, w, h) of the bounding box coordinates, or None if not found.
    """
    if image is None:
        return None
    
    # Convert to grayscale and apply a Gaussian blur
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Binarize the image to isolate the grid
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Find the largest contour, which is likely the crossword grid
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get and return the bounding box
    x, y, w, h = cv2.boundingRect(largest_contour)
    return (x, y, w, h)

def find_and_warp_crossword_grid(image):
    """
    Finds the four corners of the crossword grid and applies a perspective transform
    to warp the grid into a perfect square.

    Args:
        image (np.ndarray): The cropped image containing just the crossword grid.

    Returns:
        The rectified (warped) image, or None on failure.
    """
    if image is None:
        return None
    
    # Convert to grayscale and apply a Gaussian blur
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use adaptive thresholding to get a clean binary image
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Find contours on the binary image
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None

    # Find the largest contour again, which should be the grid itself
    main_contour = max(contours, key=cv2.contourArea)

    # Approximate the contour to a polygon with a few corners
    perimeter = cv2.arcLength(main_contour, True)
    approx = cv2.approxPolyDP(main_contour, 0.02 * perimeter, True)

    # We expect a quadrilateral (4 corners) for the grid
    if len(approx) == 4:
        # Get the four corner points
        points = approx.reshape(4, 2)
        
        # Order the points as top-left, top-right, bottom-right, bottom-left
        # This is a common method using sum and difference of coordinates
        # Sums: top-left has min sum, bottom-right has max sum
        # Differences: top-right has min diff, bottom-left has max diff
        rect = np.zeros((4, 2), dtype="float32")
        s = points.sum(axis=1)
        rect[0] = points[np.argmin(s)] # Top-left
        rect[2] = points[np.argmax(s)] # Bottom-right
        
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)] # Top-right
        rect[3] = points[np.argmax(diff)] # Bottom-left
        
        # Get the dimensions of the square to warp to
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # Define the destination points for the warp
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # Get the perspective transform matrix and warp the image
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    else:
        print(f"Detected {len(approx)} corners, not 4. Cannot warp.")
        return None

def detect_crossword_grid(image):
    """
    Detects crossword grid automatically and outputs:
    - matrix: 0 = black cell, 1 = answer cell
    - overlay: original image with detected grid lines drawn

    Parameters:
        image (numpy.ndarray): Input crossword image (cv2.imread).

    Returns:
        tuple: (matrix, overlay_image)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Binarize (invert so lines are white)
    binary = cv2.adaptiveThreshold(~gray, 255, 
                                   cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY, 15, -2)

    # Extract vertical lines
    vertical = binary.copy()
    cols = vertical.shape[1]
    vertical_size = cols // 30
    vertical_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_size))
    vertical = cv2.erode(vertical, vertical_structure)
    vertical = cv2.dilate(vertical, vertical_structure)

    # Extract horizontal lines
    horizontal = binary.copy()
    rows = horizontal.shape[0]
    horizontal_size = rows // 30
    horizontal_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    horizontal = cv2.erode(horizontal, horizontal_structure)
    horizontal = cv2.dilate(horizontal, horizontal_structure)

    # Combine grid
    grid = cv2.add(horizontal, vertical)

    # Find vertical/horizontal line positions
    vertical_sum = np.sum(vertical, axis=0)
    horizontal_sum = np.sum(horizontal, axis=1)

    x_positions = np.where(vertical_sum > vertical_sum.max() * 0.5)[0]
    y_positions = np.where(horizontal_sum > horizontal_sum.max() * 0.5)[0]

    # Collapse nearby indices into single line positions
    def collapse_positions(pos_list, min_gap=5):
        collapsed = []
        current_group = []
        for p in pos_list:
            if not current_group or p - current_group[-1] <= min_gap:
                current_group.append(p)
            else:
                collapsed.append(int(np.mean(current_group)))
                current_group = [p]
        if current_group:
            collapsed.append(int(np.mean(current_group)))
        return collapsed

    x_lines = collapse_positions(x_positions)
    y_lines = collapse_positions(y_positions)

    n_rows = len(y_lines) - 1
    n_cols = len(x_lines) - 1
    matrix = np.zeros((n_rows, n_cols), dtype=int)

    # Copy for overlay
    overlay = image.copy()

    # Check each cell
    for r in range(n_rows):
        for c in range(n_cols):
            y1, y2 = y_lines[r], y_lines[r+1]
            x1, x2 = x_lines[c], x_lines[c+1]
            cell = gray[y1:y2, x1:x2]
            mean_val = np.mean(cell)
            if mean_val < 128:  # tweak threshold if needed
                matrix[r, c] = 0
            else:
                matrix[r, c] = 1

    # Draw detected grid lines on overlay
    for x in x_lines:
        cv2.line(overlay, (x, 0), (x, overlay.shape[0]), (0, 0, 255), 1)
    for y in y_lines:
        cv2.line(overlay, (0, y), (overlay.shape[1], y), (0, 0, 255), 1)

    return matrix, overlay

def number_crossword_grid(matrix):
    """
    Takes a 0/1 crossword matrix and assigns clue numbers.
    
    Returns:
        numbers_matrix (2D array): same shape as matrix, 0 = no number, >0 = clue number
        across_clues (list): list of (num, row, col)
        down_clues (list): list of (num, row, col)
    """
    n_rows, n_cols = matrix.shape
    numbers_matrix = np.zeros_like(matrix, dtype=int)
    across_clues = []
    down_clues = []
    
    clue_num = 1
    for r in range(n_rows):
        for c in range(n_cols):
            if matrix[r, c] == 0:
                continue  # black square
            
            starts_across = (c == 0 or matrix[r, c-1] == 0) and (c+1 < n_cols and matrix[r, c+1] == 1)
            starts_down   = (r == 0 or matrix[r-1, c] == 0) and (r+1 < n_rows and matrix[r+1, c] == 1)
            
            if starts_across or starts_down:
                numbers_matrix[r, c] = clue_num
                if starts_across:
                    across_clues.append((clue_num, r, c))
                if starts_down:
                    down_clues.append((clue_num, r, c))
                clue_num += 1
    
    return numbers_matrix, across_clues, down_clues

# Utility function to draw bounding box on image for visualization
def draw_bounding_box(image, bounding_box_coords, color=(0, 255, 0), thickness=2):
    try:
        x, y, w, h = bounding_box_coords
        cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)
        return image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_crossword_grid_array(image):
    """
    End-to-end wrapper to detect crossword grid and return:
    - grid_matrix: 0 = black cell, 1 = answer cell
    - number_matrix: 0 = no clue number, >0 = clue number
    - across_clues, down_clues (lists of clue starts)
    
    Args:
        image (np.ndarray): OpenCV image array (BGR).
    
    Returns:
        tuple: (grid_matrix, number_matrix, across_clues, down_clues)
    """
    if image is None or not isinstance(image, np.ndarray):
        raise ValueError("Input must be a valid OpenCV image (numpy.ndarray)")

    # Step 1: find bounding box
    grid_bbox = find_crossword_bounding_box(image)
    if grid_bbox is None:
        raise RuntimeError("Failed to find crossword bounding box")
    x, y, w, h = grid_bbox

    cropped = image[y:y+h, x:x+w]

    # Step 2: warp
    warped = find_and_warp_crossword_grid(cropped)
    if warped is None:
        raise RuntimeError("Failed to warp crossword grid")

    # Step 3: detect grid (matrix + overlay)
    grid_matrix, overlay = detect_crossword_grid(warped)

    # Step 4: assign clue numbers
    number_matrix, across_clues, down_clues = number_crossword_grid(grid_matrix)

    return grid_matrix, number_matrix, across_clues, down_clues, grid_bbox


# Example usage
image_file_name = Path('dataset/images/daily-1994-02-Feb0494.png')
output_warped_image_path = Path('grid-detection/crossword_warped.png')
output_bbox_image_path = Path('grid-detection/crossword_detected.png')

# Load the original image
original_image = cv2.imread(str(image_file_name))

if original_image is not None:
    # Step 1: Find the bounding box of the crossword
    bounding_box_coords = find_crossword_bounding_box(original_image)
    
    if bounding_box_coords:
        x, y, w, h = bounding_box_coords
        print(f"Bounding box found: x={x}, y={y}, width={w}, height={h}")

        # Draw the bounding box on the original image for visualization
        processed_image = draw_bounding_box(original_image.copy(), bounding_box_coords)
        if processed_image is not None:
            cv2.imwrite(output_bbox_image_path, processed_image)
            print(f"Image with bounding box saved to {output_bbox_image_path}")

        # Crop the original image to just the crossword grid
        cropped_image = original_image[y:y+h, x:x+w]
        
        # Step 2: Find the 4 corners and warp the cropped image
        warped_image = find_and_warp_crossword_grid(cropped_image)
        # cv2.imwrite(str(output_warped_image_path), warped_image)
        
        if warped_image is not None:
            # Detect and draw the grid lines on the image
            grid_image = detect_crossword_grid(warped_image)
            
            if grid_image is not None:
                # cv2.imwrite(str(output_warped_image_path), grid_image)
                print(f"Final grid lines detected and saved to {output_warped_image_path}")

                matrix, overlay = detect_crossword_grid(warped_image)
                print(matrix)
                cv2.imwrite('grid-detection/crossword_overlay.png', overlay)
            else:
                print("Failed to detect grid lines on the warped image.")

        else:
            print("Failed to warp the image. Check if 4 corners were detected.")

    else:
        print("Failed to find the crossword bounding box.")

else:
    print(f"Error: Could not load image from {image_file_name}")