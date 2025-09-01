#!/bin/bash
set -e

# Cannot just pip install, the dependencies won’t work in Lambda.
# You need to build them inside an Amazon Linux 2 environment

# How to use

# 1. Make this file executable: chmod +x build_layer.sh
# 2. Run it: ./build_layer.sh
# 3. You’ll get a opencv-numpy.zip in your current directory.

# === Config ===
LAYER_NAME="opencv-numpy"
PYTHON_VERSION="3.11"   # Use 3.9 or 3.11 (3.10 not available on AL2023)
OUTPUT_ZIP="${LAYER_NAME}.zip"

echo "[INFO] Starting build for Lambda Layer: $LAYER_NAME with Python ${PYTHON_VERSION} (Amazon Linux 2023)"

docker run --rm -v $(pwd):/out public.ecr.aws/amazonlinux/amazonlinux:2023 /bin/bash -c "
    set -e
    dnf update -y
    dnf install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-devel python${PYTHON_VERSION}-pip gcc gcc-c++ make zip

    # Make sure pip is fresh
    python${PYTHON_VERSION} -m pip install --upgrade pip

    # Create layer structure
    mkdir -p /tmp/python

    # Install numpy + opencv into layer
    python${PYTHON_VERSION} -m pip install --no-cache-dir numpy opencv-python-headless -t /tmp/python

    # Zip it up
    cd /tmp
    zip -r9 /out/${OUTPUT_ZIP} python
"

echo "[INFO] Layer build complete: ${OUTPUT_ZIP}"
