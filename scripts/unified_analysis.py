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
import matplotlib.pyplot as plt
from collections import defaultdict
from utils.simple_eval import (
    analyze_spatial_correlation, 
    analyze_type_metrics,
    compute_stroke_statistics,
    compute_temporal_correlation,
    color_count,
    brush_count
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
        "total_strokes": len(strokes),
        "temporal_correlation": compute_temporal_correlation(strokes, type="color_and_brush"),
        "temporal_correlation_color": compute_temporal_correlation(strokes, type="color"),
        "temporal_correlation_brush": compute_temporal_correlation(strokes, type="brush"),
        "color_count": color_count(strokes),
        "brush_count": brush_count(strokes)
    }
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
        
        # Only take the last 10 directories (most recent)
        valid_dirs = valid_dirs[-10:] if len(valid_dirs) > 10 else valid_dirs
        
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

def main():
    """Run analysis on sample files from each dataset"""
    datasets = {
        "human": "../human/json",
        "custom": "output", 
        "random": "../random/json"
    }
    
    print("Dataset Comparison Analysis")
    print("=" * 50)
    
    all_results = []
    
    for dataset_type, base_dir in datasets.items():
        print(f"\n{dataset_type.upper()} Dataset:")
        print("-" * 20)
        
        try:
            # Get 3 sample files
            files = get_files_to_process(dataset_type, base_dir)[:3]
            
            for file_path, file_id in files:
                # Load and preprocess JSON
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                
                strokes = preprocess_json_to_stroke_format(json_data, dataset_type)
                
                if strokes:
                    result = run_eval_analysis(strokes, file_id)
                    all_results.append({**result, "dataset_type": dataset_type})
                    
                    print(f"{file_id}: {result['total_strokes']} strokes, "
                        f"temporal_corr={result['temporal_correlation']:.3f}, temporal_corr_color={result['temporal_correlation_color']:.3f}, temporal_corr_brush={result['temporal_correlation_brush']:.3f},     "
                        f"colors={result['color_count']}, brushes={result['brush_count']}")
        
        except Exception as e:
            print(f"Error processing {dataset_type}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    by_dataset = defaultdict(list)
    for r in all_results:
        by_dataset[r['dataset_type']].append(r)
    
    for dataset_type in ["human", "custom", "random"]:
        if dataset_type in by_dataset:
            results = by_dataset[dataset_type]
            avg_temporal = np.mean([r['temporal_correlation'] for r in results])
            avg_temporal_color = np.mean([r['temporal_correlation_color'] for r in results])
            avg_temporal_brush = np.mean([r['temporal_correlation_brush'] for r in results])
            avg_colors = np.mean([r['color_count'] for r in results])
            avg_brushes = np.mean([r['brush_count'] for r in results])
            print(f"{dataset_type.upper()}: temporal_corr={avg_temporal:.3f}, temporal_corr_color={avg_temporal_color:.3f}, temporal_corr_brush={avg_temporal_brush:.3f}, "
                  f"avg_colors={avg_colors:.1f}, avg_brushes={avg_brushes:.1f}")

def analyze_all_files():
    """Analyze ALL files in each dataset and compute mean/std statistics"""
    datasets = {
        "human": "../human/json",
        "custom": "output", 
        "random": "../random/json"
    }
    
    print("Complete Dataset Analysis (All Files)")
    print("=" * 60)
    
    summary_stats = {}
    
    for dataset_type, base_dir in datasets.items():
        print(f"\nProcessing ALL {dataset_type.upper()} files...")
        
        try:
            # Get ALL files (remove [:3] limit)
            all_files = get_files_to_process(dataset_type, base_dir)
            
            results = []
            processed = 0
            
            for file_path, file_id in all_files:
                try:
                    with open(file_path, 'r') as f:
                        json_data = json.load(f)
                    
                    strokes = preprocess_json_to_stroke_format(json_data, dataset_type)
                    
                    if strokes:
                        result = run_eval_analysis(strokes, file_id)
                        results.append(result)
                        processed += 1
                        
                except Exception as e:
                    print(f"  Error processing {file_id}: {e}")
                    continue
            
            if results:
                # Calculate statistics
                temporal_vals = [r['temporal_correlation'] for r in results]
                temporal_color_vals = [r['temporal_correlation_color'] for r in results]
                temporal_brush_vals = [r['temporal_correlation_brush'] for r in results]
                color_vals = [r['color_count'] for r in results]
                brush_vals = [r['brush_count'] for r in results]
                stroke_vals = [r['total_strokes'] for r in results]
                
                stats = {
                    'files_processed': processed,
                    'temporal_correlation': {'mean': np.mean(temporal_vals), 'std': np.std(temporal_vals)},
                    'temporal_correlation_color': {'mean': np.mean(temporal_color_vals), 'std': np.std(temporal_color_vals)},
                    'temporal_correlation_brush': {'mean': np.mean(temporal_brush_vals), 'std': np.std(temporal_brush_vals)},
                    
                    'color_count': {'mean': np.mean(color_vals), 'std': np.std(color_vals)},
                    'brush_count': {'mean': np.mean(brush_vals), 'std': np.std(brush_vals)},
                    'total_strokes': {'mean': np.mean(stroke_vals), 'std': np.std(stroke_vals)}
                }
                
                summary_stats[dataset_type] = stats
                
                print(f"  Processed {processed} files")
                print(f"  Temporal correlation: {stats['temporal_correlation']['mean']:.3f} ± {stats['temporal_correlation']['std']:.3f}")
                print(f"  Temporal correlation color: {stats['temporal_correlation_color']['mean']:.3f} ± {stats['temporal_correlation_color']['std']:.3f}")
                print(f"  Temporal correlation brush: {stats['temporal_correlation_brush']['mean']:.3f} ± {stats['temporal_correlation_brush']['std']:.3f}")
                print(f"  Color count: {stats['color_count']['mean']:.1f} ± {stats['color_count']['std']:.1f}")
                print(f"  Brush count: {stats['brush_count']['mean']:.1f} ± {stats['brush_count']['std']:.1f}")
                print(f"  Strokes per drawing: {stats['total_strokes']['mean']:.1f} ± {stats['total_strokes']['std']:.1f}")
            
        except Exception as e:
            print(f"  Error processing {dataset_type} dataset: {e}")
    
    # Final comparison table
    print("\n" + "=" * 60)
    print("DATASET COMPARISON (mean ± std)")
    print("=" * 60)
    print(f"{'Dataset':<10} {'Files':<6} {'Temporal Corr':<15} {'Temporal Color':<15} {'Temporal Brush':<15} {'Colors':<12} {'Brushes':<12}")
    print("-" * 60)
    
    for dataset_type in ["human", "custom", "random"]:
        if dataset_type in summary_stats:
            s = summary_stats[dataset_type]
            print(f"{dataset_type.upper():<10} {s['files_processed']:<6} "
                  f"{s['temporal_correlation']['mean']:.3f}±{s['temporal_correlation']['std']:.3f}     "
                  f"{s['temporal_correlation_color']['mean']:.3f}±{s['temporal_correlation_color']['std']:.3f}     "
                  f"{s['temporal_correlation_brush']['mean']:.3f}±{s['temporal_correlation_brush']['std']:.3f}     "
                  f"{s['color_count']['mean']:.1f}±{s['color_count']['std']:.1f}      "
                  f"{s['brush_count']['mean']:.1f}±{s['brush_count']['std']:.1f}")
    
    return summary_stats

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        analyze_all_files()
    else:
        main()