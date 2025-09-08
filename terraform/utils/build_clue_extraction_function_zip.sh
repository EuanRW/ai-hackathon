#!/bin/bash
set -e

FUNCTION_DIR="../../clue-extraction"
OUTPUT_ZIP="clue-extraction-function.zip"

echo "[INFO] Creating $OUTPUT_ZIP..."
rm -f "$OUTPUT_ZIP"
cd "$FUNCTION_DIR"
zip -r "../terraform/utils/$OUTPUT_ZIP" .
cd ..

echo "[INFO] Lambda function zip created: $OUTPUT_ZIP"
