import boto3
import cv2
import numpy as np
from grid_detect import get_crossword_grid_array

s3 = boto3.client("s3")

def lambda_handler(event, context):
    try:
        bucket = event["bucket"]
        key = event["key"]

        # Download from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        img_bytes = obj["Body"].read()

        np_arr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Unpack the new return values
        grid_matrix, number_matrix, across_clues, down_clues, grid_bbox = get_crossword_grid_array(image)

        return {
            "statusCode": 200,
            "grid_matrix": grid_matrix.tolist(),
            "number_matrix": number_matrix.tolist(),
            "across_clues": across_clues,
            "down_clues": down_clues,
            "grid_bbox": grid_bbox     
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e)
        }
