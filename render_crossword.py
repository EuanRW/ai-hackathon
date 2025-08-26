import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps

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


def render_crossword(puzzle, out_prefix):
    OUT_IMG_DIR = "dataset/images"
    OUT_MASK_DIR = "dataset/masks"

    IMG_SIZE = 512  # output square size
    CELL_PADDING = 2

    os.makedirs(OUT_IMG_DIR, exist_ok=True)
    os.makedirs(OUT_MASK_DIR, exist_ok=True)
    
    nrows, ncols = puzzle.height, puzzle.width
    cell_size = IMG_SIZE // max(nrows, ncols)

    img = Image.new("RGB", (ncols*cell_size, nrows*cell_size), "white")
    mask = Image.new("L", (ncols*cell_size, nrows*cell_size), 0)  # 0 = background, 255 = black square
    draw = ImageDraw.Draw(img)
    mask_draw = ImageDraw.Draw(mask)

    # Random font for clue numbers/letters
    num_font = load_random_font(int(cell_size * 0.3))
    letter_font = load_random_font(int(cell_size * 0.6))

    # Loop through cells
    solution = puzzle.solution
    for r in range(nrows):
        for c in range(ncols):
            idx = r * ncols + c
            x0, y0 = c*cell_size, r*cell_size
            x1, y1 = x0+cell_size, y0+cell_size

            # Black square
            if solution[idx] == ".":
                draw.rectangle([x0, y0, x1, y1], fill="black")
                mask_draw.rectangle([x0, y0, x1, y1], fill=255)
            else:
                draw.rectangle([x0, y0, x1, y1], outline="black", width=2)
                
                # Randomly decide to render the solution letter
                if random.random() > 0.5:
                    letter = solution[idx]
                    bbox = draw.textbbox((0, 0), letter, font=letter_font)
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                    draw.text(
                        (x0 + (cell_size - w) / 2, y0 + (cell_size - h) / 2),
                        letter, font=letter_font, fill="black"
                    )

    # Resize to consistent size
    img = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    mask = mask.resize((IMG_SIZE, IMG_SIZE), Image.NEAREST)

    # Add noise/augmentations
    if random.random() > 0.5:
        img = ImageOps.equalize(img)
    if random.random() > 0.5:
        img = ImageOps.autocontrast(img)
    if random.random() > 0.5:
        img = ImageOps.solarize(img, threshold=128)

    # Save
    img.save(f"{OUT_IMG_DIR}/{out_prefix}.png")
    mask.save(f"{OUT_MASK_DIR}/{out_prefix}.png")


