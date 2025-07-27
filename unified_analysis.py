#!/usr/bin/env python3
"""
Unified script to test and evaluate JSON files from both custom and human datasets.
Focuses only on metrics from utils/simple_eval.py.
"""

import os
import json
import glob
import argparse
from typing import List, Dict, Any, Tuple
import numpy as np
from utils.simple_eval import (
    analyze_spatial_correlation, 
    spatial_grouping_by
)

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
    
    if not os.path.exists(base_dir):
        print(f"Warning: Directory {base_dir} does not exist")
        return valid_dirs
        
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            if len(item) == 15 and '_' in item:  # Format: YYYYMMDD_HHMMSS
                if item > threshold_timestamp:
                    valid_dirs.append(item_path)
    
    return sorted(valid_dirs)

def preprocess_json_to_stroke_format(json_data: Dict[str, Any], dataset_type: str) -> List[Dict[str, Any]]:
    """
    Preprocess JSON data to extract stroke data in the format expected by eval functions.
    Handles custom, human, and random JSON formats.
    
    Args:
        json_data: Raw JSON data from the drawing log
        dataset_type: Either "custom", "human", or "random" to determine parsing method
        
    Returns:
        List of stroke dictionaries in format expected by eval functions
    """
    processed_strokes = []
    
    if dataset_type == "custom":
        # Custom format: nested in drawing_instructions
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
    
    elif dataset_type == "random":
        # Random format: same as custom format (nested in drawing_instructions)
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
    
    elif dataset_type == "human":
        # Human format: direct strokes array
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
    
    else:
        raise ValueError(f"Unknown dataset_type: {dataset_type}")
    
    return processed_strokes

def run_eval_analysis(strokes: List[Dict[str, Any]], file_id: str) -> Dict[str, Any]:
    """
    Run analysis using only the functions from utils/simple_eval.py.
    
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
        results["spatial_correlation"] = {
            "mean_distance": float(spatial_correlation)
        }
    except Exception as e:
        print(f"Error in spatial correlation analysis for {file_id}: {e}")
        results["spatial_correlation"] = {}
    
    # Color-based spatial grouping using spatial_grouping_by
    try:
        color_clusters = spatial_grouping_by(strokes, type="color")
        results["color_clustering"] = {}
        for color_group, cluster_info in color_clusters.items():
            results["color_clustering"][color_group] = {
                "mean_distance": float(cluster_info["mean_distance"]),
                "num_pairs": cluster_info["num_pairs"]
            }
    except Exception as e:
        print(f"Error in color clustering for {file_id}: {e}")
        results["color_clustering"] = {}
    
    # Brush-based spatial grouping using spatial_grouping_by
    try:
        brush_clusters = spatial_grouping_by(strokes, type="brush")
        results["brush_clustering"] = {}
        for brush, cluster_info in brush_clusters.items():
            results["brush_clustering"][brush] = {
                "mean_distance": float(cluster_info["mean_distance"]),
                "num_pairs": cluster_info["num_pairs"]
            }
    except Exception as e:
        print(f"Error in brush clustering for {file_id}: {e}")
        results["brush_clustering"] = {}
    
    return results

def get_files_to_process(dataset_type: str, base_dir: str, threshold_timestamp: str = None) -> List[Tuple[str, str]]:
    """
    Get list of files to process based on dataset type.
    
    Args:
        dataset_type: "custom", "human", or "random"
        base_dir: Base directory to search
        threshold_timestamp: For custom data, only process files after this timestamp
        
    Returns:
        List of tuples (file_path, file_id)
    """
    files_to_process = []
    
    if dataset_type == "custom":
        # Get directories after threshold timestamp
        valid_dirs = filter_directories_after_timestamp(base_dir, threshold_timestamp or "20250726_003439")
        
        for dir_path in valid_dirs:
            dir_name = os.path.basename(dir_path)
            json_files = glob.glob(os.path.join(dir_path, "*_complete_log.json"))
            
            if json_files:
                files_to_process.append((json_files[0], dir_name))
    
    elif dataset_type in ["human", "random"]:
        # Get all JSON files in directory
        json_files = glob.glob(os.path.join(base_dir, "*.json"))
        json_files.sort()
        
        for json_file in json_files:
            file_name = os.path.basename(json_file)
            file_id = os.path.splitext(file_name)[0]  # Remove .json extension
            files_to_process.append((json_file, file_id))
    
    else:
        raise ValueError(f"Unknown dataset_type: {dataset_type}")
    
    return files_to_process

def analyze_dataset(dataset_type: str, base_dir: str, output_dir: str, threshold_timestamp: str = None) -> List[Dict[str, Any]]:
    """
    Analyze a complete dataset (custom, human, or random).
    
    Args:
        dataset_type: "custom", "human", or "random"
        base_dir: Directory containing the data
        output_dir: Directory to save results
        threshold_timestamp: For custom data, filter by timestamp
        
    Returns:
        List of analysis results
    """
    print(f"=== Analyzing {dataset_type.upper()} Dataset ===")
    
    # Get files to process
    files_to_process = get_files_to_process(dataset_type, base_dir, threshold_timestamp)
    print(f"Found {len(files_to_process)} files to process")
    
    if not files_to_process:
        print(f"No files found for {dataset_type} dataset")
        return []
    
    all_results = []
    
    for json_file, file_id in files_to_process:
        print(f"Processing: {file_id}")
        
        try:
            # Load and preprocess JSON data
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            strokes = preprocess_json_to_stroke_format(json_data, dataset_type)
            print(f"  Extracted {len(strokes)} strokes")
            
            if len(strokes) == 0:
                print(f"  No strokes found in {file_id}")
                continue
            
            # Run eval analysis
            results = run_eval_analysis(strokes, file_id)
            
            all_results.append(results)
            print(f"  Analysis complete for {file_id}")
            
        except Exception as e:
            print(f"  Error processing {file_id}: {e}")
            continue
    
    # Save results
    if all_results:
        output_file = os.path.join(output_dir, f"{dataset_type}_eval_results.json")
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"Results saved to: {output_file}")
        
        # Print summary statistics
        print(f"\n=== {dataset_type.upper()} DATA STATISTICS ===")
        print(f"Total files processed: {len(all_results)}")
        print(f"Average strokes per file: {np.mean([r['total_strokes'] for r in all_results]):.2f}")
        
        # Spatial correlation statistics
        spatial_corrs = [r.get("spatial_correlation", {}).get("mean_distance") 
                        for r in all_results if r.get("spatial_correlation", {}).get("mean_distance") is not None]
        if spatial_corrs:
            print(f"Average spatial correlation: {np.mean(spatial_corrs):.3f} ± {np.std(spatial_corrs):.3f}")
        
        # Color clustering statistics
        color_distances = []
        for r in all_results:
            for color_group, info in r.get("color_clustering", {}).items():
                if info.get("mean_distance") is not None:
                    color_distances.append(info["mean_distance"])
        if color_distances:
            print(f"Average color group distance: {np.mean(color_distances):.3f} ± {np.std(color_distances):.3f}")
        
        # Brush clustering statistics  
        brush_distances = []
        for r in all_results:
            for brush, info in r.get("brush_clustering", {}).items():
                if info.get("mean_distance") is not None:
                    brush_distances.append(info["mean_distance"])
        if brush_distances:
            print(f"Average brush distance: {np.mean(brush_distances):.3f} ± {np.std(brush_distances):.3f}")
    
    return all_results

def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description="Unified analysis script for custom, human, and random datasets")
    parser.add_argument("--dataset", choices=["custom", "human", "random", "all"], default="all",
                       help="Which dataset to analyze (default: all)")
    parser.add_argument("--custom-dir", default="../output/custom",
                       help="Directory containing custom output data")
    parser.add_argument("--human-dir", default="../human/json", 
                       help="Directory containing human JSON data")
    parser.add_argument("--random-dir", default="../random/json",
                       help="Directory containing random JSON data")
    parser.add_argument("--output-dir", default="../output/stats",
                       help="Directory to save analysis results")
    parser.add_argument("--threshold", default="20250726_003439",
                       help="Timestamp threshold for custom data")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    results = {}
    
    # Analyze datasets based on arguments
    if args.dataset in ["custom", "all"]:
        custom_results = analyze_dataset("custom", args.custom_dir, args.output_dir, args.threshold)
        results["custom"] = custom_results
    
    if args.dataset in ["human", "all"]:
        human_results = analyze_dataset("human", args.human_dir, args.output_dir)
        results["human"] = human_results
    
    if args.dataset in ["random", "all"]:
        random_results = analyze_dataset("random", args.random_dir, args.output_dir)
        results["random"] = random_results
    
    print(f"\n=== Analysis Complete ===")
    print(f"Results saved in: {args.output_dir}")
    
    return results

def analyze_single_examples():
    """Analyze a single example from each dataset type for comparison."""
    print("\n=== Analyzing Single Examples ===")
    
    results = {}
    
    # Custom dataset example
    custom_dir = "../output/custom"
    if os.path.exists(custom_dir):
        custom_files = get_files_to_process("custom", custom_dir)
        if custom_files:
            file_path, file_id = custom_files[0]  # Get first file
            with open(file_path) as f:
                json_data = json.load(f)
            strokes = preprocess_json_to_stroke_format(json_data, "custom")
            results["custom"] = run_eval_analysis(strokes, file_id)
    
    # Human dataset example
    human_dir = "../human/json"
    if os.path.exists(human_dir):
        human_files = get_files_to_process("human", human_dir)
        if human_files:
            file_path, file_id = human_files[0]  # Get first file
            with open(file_path) as f:
                json_data = json.load(f)
            strokes = preprocess_json_to_stroke_format(json_data, "human")
            results["human"] = run_eval_analysis(strokes, file_id)
    
    # Random dataset example
    random_dir = "../random/json"
    if os.path.exists(random_dir):
        random_files = get_files_to_process("random", random_dir)
        if random_files:
            file_path, file_id = random_files[0]  # Get first file
            with open(file_path) as f:
                json_data = json.load(f)
            strokes = preprocess_json_to_stroke_format(json_data, "random")
            results["random"] = run_eval_analysis(strokes, file_id)
    
    return results

if __name__ == "__main__":
    # main() 
    results = analyze_single_examples()
    print(results)