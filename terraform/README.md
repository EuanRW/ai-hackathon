# Deploying

1. Configure AWS credentials:

   ```bash
    aws configure
   ```

2. Build function zip:

   ```bash
    cd utils
    ./build_grid_detection_function_zip.sh
   ```

3. Build opencv and numpy layer zip:

   ```bash
    ./build_opencv_numpy_layer_zip.sh.sh
   ```

4. Apply changes:

   ```bash
    terraform apply
   ```
