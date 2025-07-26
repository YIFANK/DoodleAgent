#!/usr/bin/env python3
"""
Comprehensive analysis script that runs both custom and human analyses
and compiles comparative statistics based only on utils/eval.py metrics.
"""

import os
import json
import subprocess
import pandas as pd
import numpy as np
from typing import Dict, List, Any

def run_analysis_scripts():
    """Run both analysis scripts."""
    print("=== Running Custom Output Analysis ===")
    try:
        result = subprocess.run(['python', 'test_custom_outputs.py'], 
                              capture_output=True, text=True, cwd='.')
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        custom_success = result.returncode == 0
    except Exception as e:
        print(f"Error running custom analysis: {e}")
        custom_success = False
    
    print("\n=== Running Human Output Analysis ===")
    try:
        result = subprocess.run(['python', 'test_human_outputs.py'], 
                              capture_output=True, text=True, cwd='.')
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        human_success = result.returncode == 0
    except Exception as e:
        print(f"Error running human analysis: {e}")
        human_success = False
    
    return custom_success, human_success

def load_analysis_results(stats_dir: str) -> tuple:
    """Load the results from both analyses."""
    custom_detailed = None
    human_detailed = None
    
    # Load detailed results
    custom_detailed_path = os.path.join(stats_dir, "custom_eval_results.json")
    if os.path.exists(custom_detailed_path):
        with open(custom_detailed_path, 'r') as f:
            custom_detailed = json.load(f)
    
    human_detailed_path = os.path.join(stats_dir, "human_eval_results.json")
    if os.path.exists(human_detailed_path):
        with open(human_detailed_path, 'r') as f:
            human_detailed = json.load(f)
    
    return custom_detailed, human_detailed

def analyze_spatial_correlation_comparison(custom_detailed: List[Dict], human_detailed: List[Dict]) -> Dict:
    """Compare spatial correlation metrics between custom and human data."""
    comparison = {
        "custom": {"mean_distances": [], "num_color_pairs": []},
        "human": {"mean_distances": [], "num_color_pairs": []}
    }
    
    # Analyze custom data
    for result in custom_detailed:
        spatial_corr = result.get("spatial_correlation", {})
        for color, metrics in spatial_corr.items():
            comparison["custom"]["mean_distances"].append(metrics["mean_distance"])
            comparison["custom"]["num_color_pairs"].append(metrics["num_pairs"])
    
    # Analyze human data
    for result in human_detailed:
        spatial_corr = result.get("spatial_correlation", {})
        for color, metrics in spatial_corr.items():
            comparison["human"]["mean_distances"].append(metrics["mean_distance"])
            comparison["human"]["num_color_pairs"].append(metrics["num_pairs"])
    
    # Calculate summary statistics
    summary = {}
    for dataset in ["custom", "human"]:
        if comparison[dataset]["mean_distances"]:
            summary[dataset] = {
                "avg_mean_distance": np.mean(comparison[dataset]["mean_distances"]),
                "std_mean_distance": np.std(comparison[dataset]["mean_distances"]),
                "total_color_pairs": len(comparison[dataset]["mean_distances"]),
                "avg_pairs_per_color": np.mean(comparison[dataset]["num_color_pairs"])
            }
        else:
            summary[dataset] = {"no_data": True}
    
    return summary

def analyze_clustering_comparison(custom_detailed: List[Dict], human_detailed: List[Dict]) -> Dict:
    """Compare clustering metrics between custom and human data."""
    comparison = {
        "color_clustering": {
            "custom": {"num_clusters": [], "avg_cluster_size": [], "intra_cluster_distances": []},
            "human": {"num_clusters": [], "avg_cluster_size": [], "intra_cluster_distances": []}
        },
        "brush_clustering": {
            "custom": {"num_clusters": [], "avg_cluster_size": [], "intra_cluster_distances": []},
            "human": {"num_clusters": [], "avg_cluster_size": [], "intra_cluster_distances": []}
        }
    }
    
    # Analyze custom data
    for result in custom_detailed:
        # Color clustering
        color_clustering = result.get("color_clustering", {})
        for color, metrics in color_clustering.items():
            comparison["color_clustering"]["custom"]["num_clusters"].append(metrics["num_clusters"])
            if metrics["cluster_sizes"]:
                comparison["color_clustering"]["custom"]["avg_cluster_size"].append(np.mean(metrics["cluster_sizes"]))
            if metrics.get("avg_intra_cluster_distance", 0) > 0:
                comparison["color_clustering"]["custom"]["intra_cluster_distances"].append(metrics["avg_intra_cluster_distance"])
        
        # Brush clustering
        brush_clustering = result.get("brush_clustering", {})
        for brush, metrics in brush_clustering.items():
            comparison["brush_clustering"]["custom"]["num_clusters"].append(metrics["num_clusters"])
            if metrics["cluster_sizes"]:
                comparison["brush_clustering"]["custom"]["avg_cluster_size"].append(np.mean(metrics["cluster_sizes"]))
            if metrics.get("avg_intra_cluster_distance", 0) > 0:
                comparison["brush_clustering"]["custom"]["intra_cluster_distances"].append(metrics["avg_intra_cluster_distance"])
    
    # Analyze human data
    for result in human_detailed:
        # Color clustering
        color_clustering = result.get("color_clustering", {})
        for color, metrics in color_clustering.items():
            comparison["color_clustering"]["human"]["num_clusters"].append(metrics["num_clusters"])
            if metrics["cluster_sizes"]:
                comparison["color_clustering"]["human"]["avg_cluster_size"].append(np.mean(metrics["cluster_sizes"]))
            if metrics.get("avg_intra_cluster_distance", 0) > 0:
                comparison["color_clustering"]["human"]["intra_cluster_distances"].append(metrics["avg_intra_cluster_distance"])
        
        # Brush clustering
        brush_clustering = result.get("brush_clustering", {})
        for brush, metrics in brush_clustering.items():
            comparison["brush_clustering"]["human"]["num_clusters"].append(metrics["num_clusters"])
            if metrics["cluster_sizes"]:
                comparison["brush_clustering"]["human"]["avg_cluster_size"].append(np.mean(metrics["cluster_sizes"]))
            if metrics.get("avg_intra_cluster_distance", 0) > 0:
                comparison["brush_clustering"]["human"]["intra_cluster_distances"].append(metrics["avg_intra_cluster_distance"])
    
    # Calculate summary statistics
    summary = {}
    for clustering_type in ["color_clustering", "brush_clustering"]:
        summary[clustering_type] = {}
        for dataset in ["custom", "human"]:
            data = comparison[clustering_type][dataset]
            if data["num_clusters"]:
                summary[clustering_type][dataset] = {
                    "avg_num_clusters": np.mean(data["num_clusters"]),
                    "std_num_clusters": np.std(data["num_clusters"]),
                    "avg_cluster_size": np.mean(data["avg_cluster_size"]) if data["avg_cluster_size"] else 0,
                    "std_cluster_size": np.std(data["avg_cluster_size"]) if data["avg_cluster_size"] else 0,
                    "avg_intra_cluster_distance": np.mean(data["intra_cluster_distances"]) if data["intra_cluster_distances"] else 0,
                    "std_intra_cluster_distance": np.std(data["intra_cluster_distances"]) if data["intra_cluster_distances"] else 0
                }
            else:
                summary[clustering_type][dataset] = {"no_data": True}
    
    return summary

def create_eval_comparison(custom_detailed: List[Dict], human_detailed: List[Dict], output_dir: str):
    """Create comparative analysis focusing only on utils/eval.py metrics."""
    
    comparison_results = {
        "analysis_timestamp": pd.Timestamp.now().isoformat(),
        "datasets": {
            "custom": {
                "count": len(custom_detailed) if custom_detailed else 0,
                "description": "AI-generated custom drawings from output/custom with timestamps after 20250726_003439"
            },
            "human": {
                "count": len(human_detailed) if human_detailed else 0,
                "description": "Human-generated drawings from human_json directory"
            }
        }
    }
    
    if custom_detailed and human_detailed:
        # Basic stroke count comparison
        custom_strokes = [r["total_strokes"] for r in custom_detailed]
        human_strokes = [r["total_strokes"] for r in human_detailed]
        
        comparison_results["stroke_count_comparison"] = {
            "custom_mean": np.mean(custom_strokes),
            "custom_std": np.std(custom_strokes),
            "human_mean": np.mean(human_strokes),
            "human_std": np.std(human_strokes)
        }
        
        # Spatial correlation comparison
        comparison_results["spatial_correlation_comparison"] = analyze_spatial_correlation_comparison(
            custom_detailed, human_detailed
        )
        
        # Clustering comparison
        comparison_results["clustering_comparison"] = analyze_clustering_comparison(
            custom_detailed, human_detailed
        )
        
        # Hue entropy comparison (only custom has this)
        custom_entropies = [r.get("hue_entropy") for r in custom_detailed if r.get("hue_entropy") is not None]
        if custom_entropies:
            comparison_results["hue_entropy_stats"] = {
                "custom_mean": np.mean(custom_entropies),
                "custom_std": np.std(custom_entropies),
                "custom_count": len(custom_entropies),
                "human_note": "No image data available for human drawings"
            }
    
    # Save comparative analysis
    comparison_file = os.path.join(output_dir, "eval_comparison.json")
    with open(comparison_file, 'w') as f:
        json.dump(comparison_results, f, indent=2)
    
    print(f"Eval-focused comparison saved to: {comparison_file}")
    
    return comparison_results

def print_eval_summary(comparison_results: Dict[str, Any]):
    """Print a summary of the eval-focused comparative analysis."""
    print("\n" + "="*60)
    print("EVAL METRICS COMPARATIVE ANALYSIS SUMMARY")
    print("="*60)
    
    datasets = comparison_results.get("datasets", {})
    print(f"Custom AI drawings: {datasets.get('custom', {}).get('count', 0)} files")
    print(f"Human drawings: {datasets.get('human', {}).get('count', 0)} files")
    
    if "stroke_count_comparison" in comparison_results:
        stroke_stats = comparison_results["stroke_count_comparison"]
        print(f"\nStrokes per drawing:")
        print(f"  Custom AI: {stroke_stats['custom_mean']:.1f} ± {stroke_stats['custom_std']:.1f}")
        print(f"  Human:     {stroke_stats['human_mean']:.1f} ± {stroke_stats['human_std']:.1f}")
    
    if "spatial_correlation_comparison" in comparison_results:
        spatial = comparison_results["spatial_correlation_comparison"]
        print(f"\nSpatial Correlation (Fréchet distances):")
        if not spatial.get("custom", {}).get("no_data"):
            custom = spatial["custom"]
            print(f"  Custom AI: {custom['avg_mean_distance']:.1f} ± {custom['std_mean_distance']:.1f} pixels")
            print(f"             ({custom['total_color_pairs']} color pairs analyzed)")
        if not spatial.get("human", {}).get("no_data"):
            human = spatial["human"]
            print(f"  Human:     {human['avg_mean_distance']:.1f} ± {human['std_mean_distance']:.1f} pixels")
            print(f"             ({human['total_color_pairs']} color pairs analyzed)")
    
    if "clustering_comparison" in comparison_results:
        clustering = comparison_results["clustering_comparison"]
        
        print(f"\nColor-based Spatial Clustering:")
        color_clust = clustering.get("color_clustering", {})
        for dataset in ["custom", "human"]:
            if not color_clust.get(dataset, {}).get("no_data"):
                data = color_clust[dataset]
                label = "Custom AI" if dataset == "custom" else "Human"
                print(f"  {label}: {data['avg_num_clusters']:.1f} ± {data['std_num_clusters']:.1f} clusters per color")
                print(f"            {data['avg_cluster_size']:.1f} ± {data['std_cluster_size']:.1f} strokes per cluster")
                if data['avg_intra_cluster_distance'] > 0:
                    print(f"            {data['avg_intra_cluster_distance']:.1f} ± {data['std_intra_cluster_distance']:.1f} pixels avg intra-cluster distance")
        
        print(f"\nBrush-based Spatial Clustering:")
        brush_clust = clustering.get("brush_clustering", {})
        for dataset in ["custom", "human"]:
            if not brush_clust.get(dataset, {}).get("no_data"):
                data = brush_clust[dataset]
                label = "Custom AI" if dataset == "custom" else "Human"
                print(f"  {label}: {data['avg_num_clusters']:.1f} ± {data['std_num_clusters']:.1f} clusters per brush")
                print(f"            {data['avg_cluster_size']:.1f} ± {data['std_cluster_size']:.1f} strokes per cluster")
                if data['avg_intra_cluster_distance'] > 0:
                    print(f"            {data['avg_intra_cluster_distance']:.1f} ± {data['std_intra_cluster_distance']:.1f} pixels avg intra-cluster distance")
    
    if "hue_entropy_stats" in comparison_results:
        entropy = comparison_results["hue_entropy_stats"]
        print(f"\nHue Entropy (Custom AI only):")
        print(f"  {entropy['custom_mean']:.4f} ± {entropy['custom_std']:.4f} bits")
        print(f"  ({entropy['custom_count']} images analyzed)")

def main():
    """Main function to run eval-focused analysis."""
    output_dir = "../output/stats"
    
    # Run both analysis scripts
    custom_success, human_success = run_analysis_scripts()
    
    if not (custom_success or human_success):
        print("Both analyses failed. Exiting.")
        return
    
    # Load results
    custom_detailed, human_detailed = load_analysis_results(output_dir)
    
    if custom_detailed is None and human_detailed is None:
        print("No analysis results found. Exiting.")
        return
    
    # Create eval-focused comparative analysis
    comparison_results = create_eval_comparison(custom_detailed, human_detailed, output_dir)
    
    # Print summary
    print_eval_summary(comparison_results)
    
    print(f"\n=== Analysis Complete ===")
    print(f"All results saved in: {output_dir}")

if __name__ == "__main__":
    main() 