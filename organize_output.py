#!/usr/bin/env python3
"""
Script to organize the output folder by creating subdirectories for different demo types
and moving files to appropriate locations.
"""

import os
import shutil
import glob

def organize_output():
    """Organize the output folder by creating subdirectories and moving files"""
    
    output_dir = "output"
    if not os.path.exists(output_dir):
        print("Output directory doesn't exist. Nothing to organize.")
        return
    
    # Create subdirectories
    subdirs = {
        "free_explorer": "Free Explorer Demo files",
        "painting_imitation": "Painting Imitation Demo files", 
        "autonomous_explorer": "Autonomous Explorer Demo files",
        "creative_explorer": "Creative Explorer Demo files",
        "test_images": "Test and demo images",
        "misc": "Miscellaneous files"
    }
    
    for subdir, description in subdirs.items():
        subdir_path = os.path.join(output_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        print(f"📁 Created: {subdir_path} ({description})")
    
    # Move files to appropriate subdirectories
    files_moved = 0
    
    # Free explorer files
    free_explorer_patterns = ["free_stage_*.png", "free_explorer_masterpiece.png"]
    for pattern in free_explorer_patterns:
        for file_path in glob.glob(os.path.join(output_dir, pattern)):
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                dest_path = os.path.join(output_dir, "free_explorer", filename)
                shutil.move(file_path, dest_path)
                print(f"📄 Moved: {filename} → free_explorer/")
                files_moved += 1
    
    # Painting imitation files
    imitation_patterns = ["imitation_stage_*.png", "imitation_final_imitation.png", "imitation_target.png"]
    for pattern in imitation_patterns:
        for file_path in glob.glob(os.path.join(output_dir, pattern)):
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                dest_path = os.path.join(output_dir, "painting_imitation", filename)
                shutil.move(file_path, dest_path)
                print(f"📄 Moved: {filename} → painting_imitation/")
                files_moved += 1
    
    # Autonomous explorer files
    autonomous_patterns = ["stage_*.png", "autonomous_explorer_final.png"]
    for pattern in autonomous_patterns:
        for file_path in glob.glob(os.path.join(output_dir, pattern)):
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                dest_path = os.path.join(output_dir, "autonomous_explorer", filename)
                shutil.move(file_path, dest_path)
                print(f"📄 Moved: {filename} → autonomous_explorer/")
                files_moved += 1
    
    # Creative explorer files
    creative_patterns = ["creative_explorer_final.png", "explorer_creation.png"]
    for pattern in creative_patterns:
        for file_path in glob.glob(os.path.join(output_dir, pattern)):
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                dest_path = os.path.join(output_dir, "creative_explorer", filename)
                shutil.move(file_path, dest_path)
                print(f"📄 Moved: {filename} → creative_explorer/")
                files_moved += 1
    
    # Test and demo images
    test_patterns = ["test_*.png", "demo_*.png", "blank_canvas.png", "current_canvas.png"]
    for pattern in test_patterns:
        for file_path in glob.glob(os.path.join(output_dir, pattern)):
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                dest_path = os.path.join(output_dir, "test_images", filename)
                shutil.move(file_path, dest_path)
                print(f"📄 Moved: {filename} → test_images/")
                files_moved += 1
    
    # Move any remaining PNG files to misc
    remaining_pngs = glob.glob(os.path.join(output_dir, "*.png"))
    for file_path in remaining_pngs:
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            dest_path = os.path.join(output_dir, "misc", filename)
            shutil.move(file_path, dest_path)
            print(f"📄 Moved: {filename} → misc/")
            files_moved += 1
    
    print(f"\n✅ Organization complete! Moved {files_moved} files.")
    print("\n📂 Current output structure:")
    print_directory_structure(output_dir)

def print_directory_structure(directory, prefix="", max_depth=3, current_depth=0):
    """Print the directory structure in a tree-like format"""
    if current_depth > max_depth:
        return
    
    items = sorted(os.listdir(directory))
    for i, item in enumerate(items):
        item_path = os.path.join(directory, item)
        is_last = i == len(items) - 1
        
        if os.path.isdir(item_path):
            print(f"{prefix}{'└── ' if is_last else '├── '}📁 {item}/")
            if current_depth < max_depth:
                new_prefix = prefix + ("    " if is_last else "│   ")
                print_directory_structure(item_path, new_prefix, max_depth, current_depth + 1)
        else:
            print(f"{prefix}{'└── ' if is_last else '├── '}📄 {item}")

if __name__ == "__main__":
    organize_output() 