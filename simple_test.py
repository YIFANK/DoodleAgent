import os
import glob
import shutil
import json

# Get all folders matching the pattern
output_folders = glob.glob("output/20250727_*")

for folder in output_folders:
    # Extract timestamp from folder name
    # Example: output/20250727_143051 -> timestamp: 143051
    folder_name = os.path.basename(folder)
    timestamp = folder_name.split('_')[1]  # Extract timestamp from folder name
    
    # Find all files in this folder
    mood_png_files = glob.glob(os.path.join(folder, "mood_*.png"))
    mp4_files = glob.glob(os.path.join(folder, "*.mp4"))
    json_files = glob.glob(os.path.join(folder, "*.json"))
    
    # Get the single mp4 and json files (since there's only one of each)
    mp4_file = mp4_files[0] if mp4_files else None
    json_file = json_files[0] if json_files else None
    
    # Process each PNG file to determine mood
    for png in mood_png_files:
        # Extract mood from filename
        # Example: mood_angry.png -> mood: angry
        png_filename = os.path.basename(png)
        if png_filename.startswith('mood_'):
            mood = png_filename[5:-4]  # Remove 'mood_' prefix and '.png' suffix
        else:
            continue  # Skip if doesn't match expected format
        
        # Create mood/timestamp folder structure
        mood_timestamp_folder = os.path.join("..", "mood", mood, timestamp)
        os.makedirs(mood_timestamp_folder, exist_ok=True)

        # Copy files to mood/timestamp folder
        shutil.copy2(png, mood_timestamp_folder)
        if mp4_file:
            shutil.copy2(mp4_file, mood_timestamp_folder)
        if json_file:
            shutil.copy2(json_file, mood_timestamp_folder)

print("Files organized by mood and timestamp in ../mood directory")
