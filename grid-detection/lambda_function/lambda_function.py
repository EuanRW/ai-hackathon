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

        matrix = get_crossword_grid_array(image)

        return {
            "statusCode": 200,
            "matrix": matrix.tolist()
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e)
        }
