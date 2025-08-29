import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np

def load_random_font(size):
    FONT_DIR = "/usr/share/fonts/truetype"

    FONTS = []
    for root, _, files in os.walk(FONT_DIR):
        for file in files:
            if file.lower().endswith(".ttf"):
                font_path = os.path.join(root, file)
                # Test if Pillow can open it
                try:
                    ImageFont.truetype(font_path, 10)
                    FONTS.append(font_path)
                except Exception:
                    continue

    font_path = random.choice(FONTS)
    return ImageFont.truetype(font_path, size)

def draw_crossword_grid(puzzle, cell_size, cell_padding=2):
    """Render the crossword grid with numbers and optional letters."""
    nrows, ncols = puzzle.height, puzzle.width
    solution = puzzle.solution

    grid_w, grid_h = ncols * cell_size, nrows * cell_size
    img = Image.new("RGB", (grid_w, grid_h), "white")
    mask = Image.new("L", (grid_w, grid_h), 0)
    draw = ImageDraw.Draw(img)
    mask_draw = ImageDraw.Draw(mask)

    num_font = load_random_font(int(cell_size * 0.25))
    letter_font = load_random_font(int(cell_size * 0.5))

    clue_num = 1
    clue_numbers = {}
    across_clues, down_clues = [], []

    for r in range(nrows):
        for c in range(ncols):
            idx = r * ncols + c
            x0, y0 = c * cell_size, r * cell_size
            x1, y1 = x0 + cell_size, y0 + cell_size

            if solution[idx] == ".":
                draw.rectangle([x0, y0, x1, y1], fill="black")
                mask_draw.rectangle([x0, y0, x1, y1], fill=255)
                continue

            draw.rectangle([x0, y0, x1, y1], outline="black", width=2)

            # Clue start?
            starts_across = (c == 0 or solution[idx-1] == ".") and (c+1 < ncols and solution[idx+1] != ".")
            starts_down   = (r == 0 or solution[idx-ncols] == ".") and (r+1 < nrows and solution[idx+ncols] != ".")

            if starts_across or starts_down:
                clue_numbers[idx] = clue_num
                draw.text((x0+cell_padding, y0+cell_padding),
                          str(clue_num), font=num_font, fill="black")

                if starts_across:
                    across_clues.append(f"{clue_num}. {puzzle.clues[len(across_clues)]}")
                if starts_down:
                    down_clues.append(f"{clue_num}. {puzzle.clues[len(across_clues)+len(down_clues)]}")

                clue_num += 1

    return img, mask, across_clues, down_clues, clue_numbers

def draw_clues_on_page(page, across_clues, down_clues, grid_height, margin_y, position="below"):
    draw = ImageDraw.Draw(page)
    clue_font = load_random_font(20)
    header_font = load_random_font(28)

    A4_WIDTH, _ = page.size
    col_width = A4_WIDTH // 2
    x_left, x_right = 100, col_width + 50

    # Start position
    if position == "above":
        y = 100
    else:
        y = margin_y + grid_height + 80

    # Across
    draw.text((x_left, y), "Across:", font=header_font, fill="black")
    y += 40
    for clue in across_clues:
        draw.text((x_left, y), clue, font=clue_font, fill="black")
        y += 28

    # Down (second column)
    if position == "above":
        y_down = 100
    else:
        y_down = margin_y + grid_height + 80

    draw.text((x_right, y_down), "Down:", font=header_font, fill="black")
    y_down += 40
    for clue in down_clues:
        draw.text((x_right, y_down), clue, font=clue_font, fill="black")
        y_down += 28

    # Return the max height used
    return max(y, y_down)

def extract_word_solutions(puzzle, clue_numbers):
    """
    Extract full word solutions from the grid based on clue start positions.
    Returns dictionaries for across and down words: {clue_number: "WORD"}
    """
    nrows, ncols = puzzle.height, puzzle.width
    solution = puzzle.solution
    across_words = {}
    down_words = {}

    for idx, number in clue_numbers.items():
        r, c = divmod(idx, ncols)

        # Across word
        if c == 0 or solution[idx-1] == ".":
            word = ""
            ci = c
            while ci < ncols and solution[r*ncols + ci] != ".":
                word += solution[r*ncols + ci]
                ci += 1
            across_words[str(number)] = word

        # Down word
        if r == 0 or solution[idx-ncols] == ".":
            word = ""
            ri = r
            while ri < nrows and solution[ri*ncols + c] != ".":
                word += solution[ri*ncols + c]
                ri += 1
            down_words[str(number)] = word

    return across_words, down_words

def save_solution_with_clues(puzzle, clue_numbers, across_clues, down_clues, out_dir, out_prefix):
    """
    Save the crossword solution, clues, and full word solutions in a JSON file.
    """
    import os, json
    os.makedirs(out_dir, exist_ok=True)

    # Save solution as a grid
    solution_grid = []
    for r in range(puzzle.height):
        row = []
        for c in range(puzzle.width):
            idx = r * puzzle.width + c
            if puzzle.solution[idx] == ".":  # black/non-answer square
                row.append(0)
            else:  # answer square
                row.append(1)
        solution_grid.append(row)

    # Extract full word solutions
    across_words, down_words = extract_word_solutions(puzzle, clue_numbers)

    # Prepare data
    data = {
        "width": puzzle.width,
        "height": puzzle.height,
        "grid": solution_grid,
        "clues": {
            "across": across_clues,
            "down": down_clues
        },
        "solutions": {
            "across": across_words,
            "down": down_words
        }
    }

    out_path = os.path.join(out_dir, f"{out_prefix}_solution.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

# Pylint “no-member” error happens because Pylint fails to detect constants defined in C extensions in PIL/Pillow.
# pylint: disable=no-member

def augment_image(img):
    # Mild rotation ±2.5°
    angle = random.uniform(-2.5, 2.5)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")

    # Slight skew
    width, height = img.size
    x_skew = random.uniform(-0.02, 0.02) * width
    y_skew = random.uniform(-0.02, 0.02) * height
    img = img.transform(
        (width, height),
        Image.AFFINE,
        (1, x_skew/height, 0, y_skew/width, 1, 0),
        resample=Image.BICUBIC,
        fillcolor="white"
    )

    # Slight brightness / contrast change
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(random.uniform(0.9, 1.1))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(random.uniform(0.9, 1.1))

    # Mild blur
    if random.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.2, 0.7)))

    # Add mild noise
    if random.random() < 0.5:
        arr = np.array(img)
        noise = np.random.randint(-10, 11, arr.shape, dtype=np.int16)
        arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)

    return img

def render_crossword(puzzle, out_prefix, out_img_dir, out_mask_dir, out_solution_dir):
    A4_WIDTH, A4_HEIGHT = 2480, 3508
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_mask_dir, exist_ok=True)

    # Grid rendering
    grid_max_width = int(A4_WIDTH * 0.8)
    cell_size = grid_max_width // max(puzzle.height, puzzle.width)
    grid_img, mask, across_clues, down_clues, clue_numbers = draw_crossword_grid(puzzle, cell_size)

    # Compose A4 page
    page = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
    margin_x = (A4_WIDTH - grid_img.width) // 2
    margin_y = 150

    # Randomly decide clue placement
    position = random.choice(["above", "below"])

    if position == "above":
        bottom_y = draw_clues_on_page(page, across_clues, down_clues, grid_img.height, margin_y, position="above")
        page.paste(grid_img, (margin_x, bottom_y + 40))  # put grid right below clues
    else:
        page.paste(grid_img, (margin_x, margin_y))
        draw_clues_on_page(page, across_clues, down_clues, grid_img.height, margin_y, position="below")

    page = augment_image(page)
    # Save outputs
    page.save(f"{out_img_dir}/{out_prefix}.png", dpi=(300,300))
    mask.save(f"{out_mask_dir}/{out_prefix}.png")
    save_solution_with_clues(puzzle, clue_numbers, across_clues, down_clues, out_solution_dir, out_prefix)

