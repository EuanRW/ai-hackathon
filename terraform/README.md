# Deploying

1. Configure AWS credentials:

   ```bash
    aws configure
   ```

2. Build function zip:

   ```bash
    ./build_function_zip.sh
   ```

3. Build opencv and numpy layer zip:

   ```bash
    ./build_layer_zip.sh
   ```

4. Apply changes:

   ```bash
    terraform apply
   ```
