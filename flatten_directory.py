import os
import shutil

def flatten_directory(src_dir, dest_dir):
    """
    Flattens all files from src_dir (including subdirectories) into dest_dir,
    with parent folder names prepended to avoid collisions.
    
    Example:
        daily/2015/01/Dec2915.puz -> daily-2015-01-Dec2915.puz
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for root, _, files in os.walk(src_dir):
        for file in files:
            # Get relative path from src_dir
            rel_path = os.path.relpath(os.path.join(root, file), src_dir)

            # Replace directory separators with '-'
            flat_name = rel_path.replace(os.sep, "-")

            # Construct destination path
            dest_path = os.path.join(dest_dir, flat_name)

            # Copy (or move) the file
            shutil.copy2(os.path.join(root, file), dest_path)
            # If you want to MOVE instead of COPY, replace above with:
            # shutil.move(os.path.join(root, file), dest_path)

            print(f"Processed: {rel_path} -> {flat_name}")

# Example usage
flatten_directory("daily", "flattened")