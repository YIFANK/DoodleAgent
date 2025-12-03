#!/usr/bin/env python3
"""
Script to test and evaluate human-generated JSON files from ../human_json directory.
Focuses only on metrics from utils/eval.py.
"""

import os
import json
import glob
from typing import List, Dict, Any
import numpy as np
from utils.eval import (
    analyze_spatial_correlation, 
    spatial_grouping_by
)
import pandas as pd

def preprocess_human_json_to_stroke_format(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Preprocess human JSON data to extract stroke data.
    Human format has a simpler structure with direct 'strokes' array.
    
    Args:
        json_data: Raw JSON data from human drawing files
        
    Returns:
        List of stroke dictionaries in format expected by eval functions
    """
    processed_strokes = []
    
    if "strokes" not in json_data:
        return processed_strokes
    
    for stroke in json_data["strokes"]:
        if "stroke" in stroke and "x" in stroke["stroke"] and "y" in stroke["stroke"]:
            processed_stroke = {
                "color": stroke.get("color", "#000000"),
                "brush": stroke.get("brush", "unknown"),
                "stroke": {
                    "x": stroke["stroke"]["x"],
                    "y": stroke["stroke"]["y"]
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

def main():
    """Main function to run the evaluation script for human JSON files."""
    
    # Configuration
    base_dir = "../human_json"
    output_dir = "../output/stats"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all JSON files in the directory
    json_files = glob.glob(os.path.join(base_dir, "*.json"))
    json_files.sort()  # Sort for consistent processing order
    
    if not json_files:
        print(f"No JSON files found in {base_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    all_results = []
    
    for json_file in json_files:
        file_name = os.path.basename(json_file)
        file_id = os.path.splitext(file_name)[0]  # Remove .json extension
        print(f"Processing file: {file_name}")
        
        try:
            # Load and preprocess JSON data
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            strokes = preprocess_human_json_to_stroke_format(json_data)
            print(f"  Extracted {len(strokes)} strokes")
            
            if len(strokes) == 0:
                print(f"  No strokes found in {file_name}")
                continue
            
            # Run eval analysis
            results = run_eval_analysis(strokes, file_id)
            
            all_results.append(results)
            print(f"  Analysis complete for {file_name}")
            
        except Exception as e:
            print(f"  Error processing {file_name}: {e}")
            continue
    
    # Save results
    if all_results:
        # Save detailed results as JSON
        output_file = os.path.join(output_dir, "human_eval_results.json")
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"Results saved to: {output_file}")
        
        print(f"\n=== HUMAN DATA OVERALL STATISTICS ===")
        print(f"Total files processed: {len(all_results)}")
        print(f"Average strokes per file: {np.mean([r['total_strokes'] for r in all_results]):.2f}")
    
    else:
        print("No results to save.")

if __name__ == "__main__":
    main() 