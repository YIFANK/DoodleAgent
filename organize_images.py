#!/usr/bin/env python3

import os
import shutil
import re
from datetime import datetime
from pathlib import Path

def parse_timestamp(folder_name):
    """Parse timestamp from folder name format YYYYMMDD_HHMMSS"""
    try:
        return datetime.strptime(folder_name, "%Y%m%d_%H%M%S")
    except ValueError:
        return None

def get_final_image(folder_path):
    """Determine the final image and generation mode for a folder"""
    files = os.listdir(folder_path)
    
    # Check for mood mode
    if any(f.startswith('mood_') for f in files):
        if 'mood_final.png' in files:
            return 'mood_final.png', 'mood'
        else:
            # Find highest numbered mood step
            mood_steps = [f for f in files if f.startswith('mood_step_') and f.endswith('.png')]
            if mood_steps:
                # Extract step numbers and find max
                step_nums = []
                for f in mood_steps:
                    match = re.search(r'mood_step_(\d+)\.png', f)
                    if match:
                        step_nums.append((int(match.group(1)), f))
                if step_nums:
                    step_nums.sort(reverse=True)
                    return step_nums[0][1], 'mood'
    
    # Check for abstract mode
    if any(f.startswith('abstract_') for f in files):
        if 'abstract_final.png' in files:
            return 'abstract_final.png', 'abstract'
        else:
            # Find highest numbered abstract step
            abstract_steps = [f for f in files if f.startswith('abstract_step_') and f.endswith('.png')]
            if abstract_steps:
                # Extract step numbers and find max
                step_nums = []
                for f in abstract_steps:
                    match = re.search(r'abstract_step_(\d+)\.png', f)
                    if match:
                        step_nums.append((int(match.group(1)), f))
                if step_nums:
                    step_nums.sort(reverse=True)
                    return step_nums[0][1], 'abstract'
    
    # Check for free mode (canvas steps)
    if any(f.startswith('canvas_step_') for f in files):
        canvas_steps = [f for f in files if f.startswith('canvas_step_') and f.endswith('.png')]
        if canvas_steps:
            # Extract step numbers and find max
            step_nums = []
            for f in canvas_steps:
                match = re.search(r'canvas_step_(\d+)\.png', f)
                if match:
                    step_nums.append((int(match.group(1)), f))
            if step_nums:
                step_nums.sort(reverse=True)
                return step_nums[0][1], 'free'
    
    return None, None

def main():
    # Configuration
    output_dir = Path('DoodleAgent/output')
    start_timestamp = "20250622_175430"
    organized_dir = Path('organized_images')
    
    # Create organized directories
    categories = ['abstract', 'mood', 'free']
    for category in categories:
        category_dir = organized_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all timestamped folders
    timestamped_folders = []
    start_dt = parse_timestamp(start_timestamp)
    
    if not start_dt:
        print(f"Error: Could not parse start timestamp {start_timestamp}")
        return
    
    for item in output_dir.iterdir():
        if item.is_dir():
            timestamp = parse_timestamp(item.name)
            if timestamp and timestamp >= start_dt:
                timestamped_folders.append((timestamp, item))
    
    # Sort by timestamp
    timestamped_folders.sort(key=lambda x: x[0])
    
    print(f"Found {len(timestamped_folders)} folders from {start_timestamp} onwards")
    
    # Process each folder
    processed_count = {'abstract': 0, 'mood': 0, 'free': 0}
    
    for timestamp, folder_path in timestamped_folders:
        folder_name = folder_path.name
        print(f"Processing {folder_name}...")
        
        final_image, mode = get_final_image(folder_path)
        
        if final_image and mode:
            source_path = folder_path / final_image
            # Create descriptive filename with timestamp and original name
            new_filename = f"{folder_name}_{final_image}"
            dest_path = organized_dir / mode / new_filename
            
            try:
                shutil.copy2(source_path, dest_path)
                processed_count[mode] += 1
                print(f"  ✓ Copied {final_image} to {mode}/ as {new_filename}")
            except Exception as e:
                print(f"  ✗ Error copying {final_image}: {e}")
        else:
            print(f"  ! No final image found or could not determine mode")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Total folders processed: {len(timestamped_folders)}")
    for category in categories:
        print(f"{category.capitalize()} images: {processed_count[category]}")
    print(f"Images organized in: {organized_dir.absolute()}")

if __name__ == "__main__":
    main() 