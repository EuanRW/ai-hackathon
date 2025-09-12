import boto3
import json
import re
from PIL import Image
import io

textract = boto3.client("textract")
s3 = boto3.client("s3")

def overlaps(block_box, exclude_box, tolerance=0.0):
    """
    Return True if block_box overlaps exclude_box.
    Each box is a dict with Left, Top, Width, Height (Textract normalized coordinates).
    """
    b_left   = block_box["Left"]
    b_right  = block_box["Left"] + block_box["Width"]
    b_top    = block_box["Top"]
    b_bottom = block_box["Top"] + block_box["Height"]

    e_left   = exclude_box["Left"] - tolerance
    e_right  = exclude_box["Left"] + exclude_box["Width"] + tolerance
    e_top    = exclude_box["Top"] - tolerance
    e_bottom = exclude_box["Top"] + exclude_box["Height"] + tolerance

    return not (b_right < e_left or b_left > e_right or b_bottom < e_top or b_top > e_bottom)

def normalize_bbox(pixel_bbox, bucket, key):
    """
    Convert a pixel-based bbox [x, y, w, h] into Textract normalized coordinates {Left, Top, Width, Height}.
    """
    # Download image from S3 to get dimensions
    s3_obj = s3.get_object(Bucket=bucket, Key=key)
    img = Image.open(io.BytesIO(s3_obj["Body"].read()))
    img_width, img_height = img.size

    x, y, w, h = pixel_bbox
    return {
        "Left": x / img_width,
        "Top": y / img_height,
        "Width": w / img_width,
        "Height": h / img_height
    }

def lambda_handler(event, context):
    # If invoked via API Gateway, body will be a JSON string
    if "body" in event:
        body = json.loads(event["body"])
    else:
        body = event  # direct invocation

    bucket = body["bucket"]
    key = body["key"]

    # Optional: exclusion area for crossword grid
    grid_bbox = body.get("grid_bbox")  # may be list [x,y,w,h] or dict
    if grid_bbox:
        if isinstance(grid_bbox, list) and len(grid_bbox) == 4:
            grid_bbox = normalize_bbox(grid_bbox, bucket, key)
        elif not isinstance(grid_bbox, dict):
            raise ValueError("grid_bbox must be either a dict {Left,Top,Width,Height} or list [x,y,w,h]")

    TOLERANCE = 0.05

    response = textract.analyze_document(
        Document={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["LAYOUT"]
    )

    lines = []
    across_header_left = None
    down_header_left = None

    for block in response["Blocks"]:
        if block["BlockType"] == "LINE":
            # Skip if block falls inside the crossword grid
            if grid_bbox and overlaps(block["Geometry"]["BoundingBox"], grid_bbox):
                continue

            text = block.get("Text", "").strip()
            if not text:
                continue

            if re.match(r'^\s*Across[:\s]*$', text, re.IGNORECASE):
                across_header_left = block["Geometry"]["BoundingBox"]["Left"]
                continue
            if re.match(r'^\s*Down[:\s]*$', text, re.IGNORECASE):
                down_header_left = block["Geometry"]["BoundingBox"]["Left"]
                continue

            # Only keep lines that look like clues (start with a number)
            if not re.match(r'^\d', text):
                continue

            lines.append({
                "text": text,
                "top": block["Geometry"]["BoundingBox"]["Top"],
                "left": block["Geometry"]["BoundingBox"]["Left"]
            })

    # Sort by vertical position, then left position
    lines = sorted(lines, key=lambda x: (x["top"], x["left"]))

    across_clues, down_clues = [], []

    for line in lines:
        if down_header_left is not None and line["left"] >= down_header_left - TOLERANCE:
            down_clues.append(line["text"])
        elif across_header_left is not None and line["left"] <= across_header_left + TOLERANCE:
            across_clues.append(line["text"])

    result = {
        "across": across_clues,
        "down": down_clues
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(result, indent=2)
    }