import boto3
import json
import re

textract = boto3.client("textract")

def lambda_handler(event, context):
    bucket = event["bucket"]
    key = event["key"]

    response = textract.analyze_document(
        Document={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["LAYOUT"]
    )

    # Collect lines with positions
    lines = []
    for block in response["Blocks"]:
        if block["BlockType"] == "LINE":
            text = block["Text"].strip()

            # 🔑 Skip lines that are just numbers (grid labels)
            if re.match(r'^\d+\.?$', text):
                continue

            lines.append({
                "text": text,
                "top": block["Geometry"]["BoundingBox"]["Top"],
                "left": block["Geometry"]["BoundingBox"]["Left"]
            })

    # Sort top-to-bottom, then left-to-right
    lines = sorted(lines, key=lambda x: (x["top"], x["left"]))

    across_clues, down_clues = [], []

    # Find median split between left/right columns
    left_positions = [line["left"] for line in lines]
    column_cutoff = (min(left_positions) + max(left_positions)) / 2

    for line in lines:
        text = line["text"]

        # Skip obvious headers
        if re.match(r'^\s*Across[:\s]*$', text, re.IGNORECASE):
            continue
        if re.match(r'^\s*Down[:\s]*$', text, re.IGNORECASE):
            continue

        # Decide column by "Left" position
        if line["left"] < column_cutoff:
            across_clues.append(text)
        else:
            down_clues.append(text)

    result = {
        "across": across_clues,
        "down": down_clues
    }

    return {
        "statusCode": 200,
        "body": json.dumps(result)  # no indent, clean single JSON
    }
