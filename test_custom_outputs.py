#!/usr/bin/env python3
"""
Script to test and evaluate JSON files from custom output directories.
Tests all JSON files with timestamps after '20250726_003439'.
Focuses only on metrics from utils/eval.py.
"""

import os
import json
import glob
from typing import List, Dict, Any
import numpy as np
from utils.eval import (
    analyze_spatial_correlation, 
    spatial_grouping_by,
    compute_hue_entropy
)
from PIL import Image
import pandas as pd

def filter_directories_after_timestamp(base_dir: str, threshold_timestamp: str) -> List[str]:
    """
    Filter directories with timestamps after the given threshold.
    
    Args:
        base_dir: Base directory containing timestamp directories
        threshold_timestamp: Timestamp string in format 'YYYYMMDD_HHMMSS'
        
    Returns:
        List of directory paths with timestamps after threshold
    """
    valid_dirs = []
    
    # Get all directories in base_dir
    if not os.path.exists(base_dir):
        print(f"Warning: Directory {base_dir} does not exist")
        return valid_dirs
        
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            # Extract timestamp from directory name
            if len(item) == 15 and '_' in item:  # Format: YYYYMMDD_HHMMSS
                if item > threshold_timestamp:
                    valid_dirs.append(item_path)
    
    return sorted(valid_dirs)

def preprocess_json_to_stroke_format(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Preprocess JSON data to extract stroke data in the format expected by eval functions.
    
    Args:
        json_data: Raw JSON data from the drawing log
        
    Returns:
        List of stroke dictionaries in format expected by eval functions
    """
    processed_strokes = []
    
    if "drawing_instructions" not in json_data:
        return processed_strokes
    
    for instruction in json_data["drawing_instructions"]:
        if "strokes" in instruction:
            color = instruction.get("color", "#000000")
            brush = instruction.get("brush", "unknown")
            
            for stroke in instruction["strokes"]:
                if "x" in stroke and "y" in stroke:
                    processed_stroke = {
                        "color": color,
                        "brush": brush,
                        "stroke": {
                            "x": stroke["x"],
                            "y": stroke["y"]
                        }
                    }
                    processed_strokes.append(processed_stroke)
    
    return processed_strokes

def run_eval_analysis(strokes: List[Dict[str, Any]], file_id: str) -> Dict[str, Any]:
    """
    Run analysis using only the functions from utils/eval.py.
    
    Args:
        strokes: List of preprocessed strokes
        file_id: Identifier for the file being analyzed
        
    Returns:
        Dictionary containing analysis results
    """
    results = {
        "file_id": file_id,
        "total_strokes": len(strokes)
    }
    
    # Spatial correlation analysis using analyze_spatial_correlation
    try:
        spatial_correlation = analyze_spatial_correlation(strokes)
        results["spatial_correlation"] = {}
        for color, distances in spatial_correlation.items():
            if distances:  # Only include colors with multiple strokes
                results["spatial_correlation"][color] = {
                    "mean_distance": float(np.mean(distances)),
                    "std_distance": float(np.std(distances)),
                    "min_distance": float(np.min(distances)),
                    "max_distance": float(np.max(distances)),
                    "num_pairs": len(distances)
                }
    except Exception as e:
        print(f"Error in spatial correlation analysis for {file_id}: {e}")
        results["spatial_correlation"] = {}
    
    # Color-based spatial grouping using spatial_grouping_by
    try:
        color_clusters = spatial_grouping_by(strokes, type="color")
        results["color_clustering"] = {}
        for color, clusters in color_clusters.items():
            cluster_sizes = [cluster_info["num_strokes"] for cluster_info in clusters.values()]
            intra_cluster_distances = [cluster_info["avg_intra_cluster_distance"] 
                                     for cluster_info in clusters.values() 
                                     if cluster_info["avg_intra_cluster_distance"] > 0]
            
            results["color_clustering"][color] = {
                "num_clusters": len(clusters),
                "cluster_sizes": cluster_sizes,
                "total_strokes": sum(cluster_sizes),
                "avg_intra_cluster_distance": float(np.mean(intra_cluster_distances)) if intra_cluster_distances else 0.0,
                "std_intra_cluster_distance": float(np.std(intra_cluster_distances)) if len(intra_cluster_distances) > 1 else 0.0
            }
    except Exception as e:
        print(f"Error in color clustering for {file_id}: {e}")
        results["color_clustering"] = {}
    
    # Brush-based spatial grouping using spatial_grouping_by
    try:
        brush_clusters = spatial_grouping_by(strokes, type="brush")
        results["brush_clustering"] = {}
        for brush, clusters in brush_clusters.items():
            cluster_sizes = [cluster_info["num_strokes"] for cluster_info in clusters.values()]
            intra_cluster_distances = [cluster_info["avg_intra_cluster_distance"] 
                                     for cluster_info in clusters.values() 
                                     if cluster_info["avg_intra_cluster_distance"] > 0]
            
            results["brush_clustering"][brush] = {
                "num_clusters": len(clusters),
                "cluster_sizes": cluster_sizes,
                "total_strokes": sum(cluster_sizes),
                "avg_intra_cluster_distance": float(np.mean(intra_cluster_distances)) if intra_cluster_distances else 0.0,
                "std_intra_cluster_distance": float(np.std(intra_cluster_distances)) if len(intra_cluster_distances) > 1 else 0.0
            }
    except Exception as e:
        print(f"Error in brush clustering for {file_id}: {e}")
        results["brush_clustering"] = {}
    
    return results

def analyze_image_hue_entropy(image_path: str) -> Dict[str, Any]:
    """
    Analyze image using compute_hue_entropy from utils/eval.py.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing hue entropy analysis
    """
    image_results = {}
    
    if os.path.exists(image_path):
        try:
            image = Image.open(image_path).convert("RGB")
            rgb_np = np.array(image)
            
            # Compute hue entropy using the function from utils/eval.py
            entropy = compute_hue_entropy(rgb_np, bins=36)
            image_results["hue_entropy"] = float(entropy)
            image_results["has_image"] = True
            
        except Exception as e:
            print(f"Error analyzing image {image_path}: {e}")
            image_results["has_image"] = False
    else:
        image_results["has_image"] = False
    
    return image_results

def main():
    """Main function to run the evaluation script."""
    
    # Configuration
    base_dir = "../output/custom"
    threshold_timestamp = "20250726_003439"
    output_dir = "../output/stats"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get directories to process
    valid_dirs = filter_directories_after_timestamp(base_dir, threshold_timestamp)
    print(f"Found {len(valid_dirs)} directories to process after {threshold_timestamp}")
    
    all_results = []
    
    for dir_path in valid_dirs:
        dir_name = os.path.basename(dir_path)
        print(f"Processing directory: {dir_name}")
        
        # Find JSON file in directory
        json_files = glob.glob(os.path.join(dir_path, "*_complete_log.json"))
        
        if not json_files:
            print(f"  No JSON file found in {dir_name}")
            continue
            
        json_file = json_files[0]  # Take the first (should be only one)
        
        try:
            # Load and preprocess JSON data
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            strokes = preprocess_json_to_stroke_format(json_data)
            print(f"  Extracted {len(strokes)} strokes")
            
            if len(strokes) == 0:
                print(f"  No strokes found in {dir_name}")
                continue
            
            # Run eval analysis
            results = run_eval_analysis(strokes, dir_name)
            
            # Analyze associated image if it exists
            image_path = os.path.join(dir_path, f"{dir_name}.png")
            image_results = analyze_image_hue_entropy(image_path)
            results.update(image_results)
            
            all_results.append(results)
            print(f"  Analysis complete for {dir_name}")
            
        except Exception as e:
            print(f"  Error processing {dir_name}: {e}")
            continue
    
    # Save results
    if all_results:
        # Save detailed results as JSON
        output_file = os.path.join(output_dir, "custom_eval_results.json")
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"Results saved to: {output_file}")
        
        print(f"\n=== OVERALL STATISTICS ===")
        print(f"Total files processed: {len(all_results)}")
        print(f"Average strokes per file: {np.mean([r['total_strokes'] for r in all_results]):.2f}")
        
        # Hue entropy statistics
        entropies = [r["hue_entropy"] for r in all_results if r.get("hue_entropy") is not None]
        if entropies:
            print(f"Average hue entropy: {np.mean(entropies):.4f} ± {np.std(entropies):.4f}")
    
    else:
        print("No results to save.")

if __name__ == "__main__":
    main() 