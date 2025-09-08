import boto3
import json
import re

textract = boto3.client("textract")

def lambda_handler(event, context):
    bucket = event["bucket"]
    key = event["key"]

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
            text = block["Text"].strip()
            
            # Find headers to define column boundaries
            if re.match(r'^\s*Across[:\s]*$', text, re.IGNORECASE):
                across_header_left = block["Geometry"]["BoundingBox"]["Left"]
                continue
            if re.match(r'^\s*Down[:\s]*$', text, re.IGNORECASE):
                down_header_left = block["Geometry"]["BoundingBox"]["Left"]
                continue
            
            # 🔑 Filter: Exclude lines that don't start with a number
            if not re.match(r'^\d', text):
                continue
            
            lines.append({
                "text": text,
                "top": block["Geometry"]["BoundingBox"]["Top"],
                "left": block["Geometry"]["BoundingBox"]["Left"]
            })

    # Sort lines
    lines = sorted(lines, key=lambda x: (x["top"], x["left"]))

    across_clues, down_clues = [], []
    
    # Assign lines to columns
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
        "body": json.dumps(result)
    }