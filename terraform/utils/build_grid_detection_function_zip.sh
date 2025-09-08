#!/bin/bash
set -e

FUNCTION_DIR="../../grid-detection/lambda_function"
OUTPUT_ZIP="grid-detect-function.zip"

echo "[INFO] Creating $OUTPUT_ZIP..."
rm -f "$OUTPUT_ZIP"
cd "$FUNCTION_DIR"
zip -r "../../terraform/utils/$OUTPUT_ZIP" .
cd ..

echo "[INFO] Lambda function zip created: $OUTPUT_ZIP"
