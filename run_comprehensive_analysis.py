#!/usr/bin/env python3
"""
Comprehensive analysis script that runs the unified analysis for both datasets
and compiles comparative statistics based only on utils/eval.py metrics.
"""

import os
import json
import subprocess
import pandas as pd
import numpy as np
from typing import Dict, List, Any

def run_unified_analysis():
    """Run the unified analysis script for all datasets."""
    print("=== Running Unified Analysis for All Datasets ===")
    try:
        result = subprocess.run(['python', 'unified_analysis.py', '--dataset', 'all'], 
                              capture_output=True, text=True, cwd='.')
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        success = result.returncode == 0
    except Exception as e:
        print(f"Error running unified analysis: {e}")
        success = False
    
    return success

def load_analysis_results(stats_dir: str) -> tuple:
    """Load the results from unified analysis."""
    custom_detailed = None
    human_detailed = None
    random_detailed = None
    
    # Load detailed results
    custom_detailed_path = os.path.join(stats_dir, "custom_eval_results.json")
    if os.path.exists(custom_detailed_path):
        with open(custom_detailed_path, 'r') as f:
            data = json.load(f)
            # Handle new format with separate stroke_analysis and image_analysis
            if isinstance(data, dict) and "stroke_analysis" in data:
                custom_detailed = data["stroke_analysis"]
            else:
                # Backward compatibility with old format
                custom_detailed = data
    
    human_detailed_path = os.path.join(stats_dir, "human_eval_results.json")
    if os.path.exists(human_detailed_path):
        with open(human_detailed_path, 'r') as f:
            data = json.load(f)
            # Handle new format with separate stroke_analysis and image_analysis
            if isinstance(data, dict) and "stroke_analysis" in data:
                human_detailed = data["stroke_analysis"]
            else:
                # Backward compatibility with old format
                human_detailed = data
    
    random_detailed_path = os.path.join(stats_dir, "random_eval_results.json")
    if os.path.exists(random_detailed_path):
        with open(random_detailed_path, 'r') as f:
            data = json.load(f)
            # Handle new format with separate stroke_analysis and image_analysis
            if isinstance(data, dict) and "stroke_analysis" in data:
                random_detailed = data["stroke_analysis"]
            else:
                # Backward compatibility with old format
                random_detailed = data
    
    return custom_detailed, human_detailed, random_detailed

def load_image_analysis_results(stats_dir: str) -> tuple:
    """Load the image analysis results from unified analysis."""
    custom_images = []
    human_images = []
    random_images = []
    
    # Load image analysis results
    custom_detailed_path = os.path.join(stats_dir, "custom_eval_results.json")
    if os.path.exists(custom_detailed_path):
        with open(custom_detailed_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "image_analysis" in data and data["image_analysis"]:
                custom_images = data["image_analysis"]
    
    human_detailed_path = os.path.join(stats_dir, "human_eval_results.json")
    if os.path.exists(human_detailed_path):
        with open(human_detailed_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "image_analysis" in data and data["image_analysis"]:
                human_images = data["image_analysis"]
    
    random_detailed_path = os.path.join(stats_dir, "random_eval_results.json")
    if os.path.exists(random_detailed_path):
        with open(random_detailed_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "image_analysis" in data and data["image_analysis"]:
                random_images = data["image_analysis"]
    
    return custom_images, human_images, random_images

def analyze_spatial_correlation_comparison(custom_detailed: List[Dict], human_detailed: List[Dict], random_detailed: List[Dict]) -> Dict:
    """Compare spatial correlation metrics between custom, human, and random data."""
    comparison = {
        "custom": {"mean_distances": [], "num_color_pairs": []},
        "human": {"mean_distances": [], "num_color_pairs": []},
        "random": {"mean_distances": [], "num_color_pairs": []}
    }

    # Analyze custom data
    # Process each dataset type
    for dataset_type, data in [("custom", custom_detailed), ("human", human_detailed), ("random", random_detailed)]:
        if data:
            for result in data:
                spatial_corr = result.get("spatial_correlation", {})
                for metrics in spatial_corr.values():
                    comparison[dataset_type]["mean_distances"].append(metrics["mean_distance"])
                    comparison[dataset_type]["num_color_pairs"].append(metrics["num_pairs"])
    
    # Calculate summary statistics
    summary = {}
    for dataset in ["custom", "human", "random"]:
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

def analyze_clustering_comparison(custom_detailed: List[Dict], human_detailed: List[Dict], random_detailed: List[Dict]) -> Dict:
    """Compare clustering metrics between custom, human, and random data."""
    comparison = {
        "color_clustering": {},
        "brush_clustering": {}
    }
    
    # Initialize metrics for each dataset type
    metrics = ["num_clusters", "avg_cluster_size", "intra_cluster_distances"]
    dataset_types = ["custom", "human", "random"]
    
    for clustering_type in ["color_clustering", "brush_clustering"]:
        comparison[clustering_type] = {
            dataset: {metric: [] for metric in metrics}
            for dataset in dataset_types
        }

    # Analyze custom data
    # Process each dataset type
    for dataset_type, dataset in [("custom", custom_detailed), ("human", human_detailed), ("random", random_detailed)]:
        if not dataset:
            continue
            
        for result in dataset:
            # Process color clustering
            color_clustering = result.get("color_clustering", {})
            for color, metrics in color_clustering.items():
                comparison["color_clustering"][dataset_type]["num_clusters"].append(metrics["num_clusters"])
                if metrics["cluster_sizes"]:
                    comparison["color_clustering"][dataset_type]["avg_cluster_size"].append(np.mean(metrics["cluster_sizes"]))
                if metrics.get("avg_intra_cluster_distance", 0) > 0:
                    comparison["color_clustering"][dataset_type]["intra_cluster_distances"].append(metrics["avg_intra_cluster_distance"])
            
            # Process brush clustering
            brush_clustering = result.get("brush_clustering", {})
            for brush, metrics in brush_clustering.items():
                comparison["brush_clustering"][dataset_type]["num_clusters"].append(metrics["num_clusters"])
                if metrics["cluster_sizes"]:
                    comparison["brush_clustering"][dataset_type]["avg_cluster_size"].append(np.mean(metrics["cluster_sizes"]))
                if metrics.get("avg_intra_cluster_distance", 0) > 0:
                    comparison["brush_clustering"][dataset_type]["intra_cluster_distances"].append(metrics["avg_intra_cluster_distance"])
    # Calculate summary statistics
    summary = {}
    for clustering_type in ["color_clustering", "brush_clustering"]:
        summary[clustering_type] = {}
        for dataset in ["custom", "human", "random"]:
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

def analyze_temporal_correlation_comparison(custom_detailed: List[Dict], human_detailed: List[Dict], random_detailed: List[Dict]) -> Dict:
    """Compare temporal correlation metrics between custom, human, and random data."""
    comparison = {
        "custom": {"autocorrelations": [], "transition_entropies": [], "repetition_ratios": [], "avg_diversities": []},
        "human": {"autocorrelations": [], "transition_entropies": [], "repetition_ratios": [], "avg_diversities": []},
        "random": {"autocorrelations": [], "transition_entropies": [], "repetition_ratios": [], "avg_diversities": []}
    }
    
    # Process each dataset type
    for dataset_type, data in [("custom", custom_detailed), ("human", human_detailed), ("random", random_detailed)]:
        if data:
            for result in data:
                temporal_corr = result.get("temporal_correlation", {})
                temporal_metrics = temporal_corr.get("temporal_metrics", {})
                
                # Collect autocorrelation values
                mean_autocorr = temporal_metrics.get("mean_autocorrelation")
                if mean_autocorr is not None:
                    comparison[dataset_type]["autocorrelations"].append(mean_autocorr)
                
                # Collect transition entropy values
                norm_entropy = temporal_metrics.get("normalized_entropy")
                if norm_entropy is not None:
                    comparison[dataset_type]["transition_entropies"].append(norm_entropy)
                
                # Collect repetition ratios
                rep_stats = temporal_metrics.get("repetition_stats", {})
                rep_ratio = rep_stats.get("repetition_ratio")
                if rep_ratio is not None:
                    comparison[dataset_type]["repetition_ratios"].append(rep_ratio)
                
                # Collect diversity measures
                div_stats = temporal_metrics.get("diversity_stats", {})
                avg_diversity = div_stats.get("avg_diversity")
                if avg_diversity is not None:
                    comparison[dataset_type]["avg_diversities"].append(avg_diversity)
    
    # Calculate summary statistics
    summary = {}
    for dataset in ["custom", "human", "random"]:
        data = comparison[dataset]
        if any(len(values) > 0 for values in data.values()):
            summary[dataset] = {}
            
            # Autocorrelation stats
            if data["autocorrelations"]:
                summary[dataset]["autocorrelation"] = {
                    "mean": float(np.mean(data["autocorrelations"])),
                    "std": float(np.std(data["autocorrelations"])),
                    "count": len(data["autocorrelations"])
                }
            
            # Transition entropy stats
            if data["transition_entropies"]:
                summary[dataset]["transition_entropy"] = {
                    "mean": float(np.mean(data["transition_entropies"])),
                    "std": float(np.std(data["transition_entropies"])),
                    "count": len(data["transition_entropies"])
                }
            
            # Repetition ratio stats
            if data["repetition_ratios"]:
                summary[dataset]["repetition_ratio"] = {
                    "mean": float(np.mean(data["repetition_ratios"])),
                    "std": float(np.std(data["repetition_ratios"])),
                    "count": len(data["repetition_ratios"])
                }
            
            # Diversity stats
            if data["avg_diversities"]:
                summary[dataset]["diversity"] = {
                    "mean": float(np.mean(data["avg_diversities"])),
                    "std": float(np.std(data["avg_diversities"])),
                    "count": len(data["avg_diversities"])
                }
        else:
            summary[dataset] = {"no_data": True}
    
    return summary

def create_eval_comparison(custom_detailed: List[Dict], human_detailed: List[Dict], random_detailed: List[Dict], output_dir: str):
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
            },
            "random": {
                "count": len(random_detailed) if random_detailed else 0,
                "description": "Random drawings from random/json directory"
            }
        }
    }
    
    # Create lists of datasets that have data
    datasets_with_data = []
    if custom_detailed:
        datasets_with_data.append(("custom", custom_detailed))
    if human_detailed:
        datasets_with_data.append(("human", human_detailed))  
    if random_detailed:
        datasets_with_data.append(("random", random_detailed))
    
    if len(datasets_with_data) >= 2:
        # Basic stroke count comparison
        stroke_comparison = {}
        for dataset_name, dataset in datasets_with_data:
            strokes = [r["total_strokes"] for r in dataset]
            stroke_comparison[f"{dataset_name}_mean"] = np.mean(strokes)
            stroke_comparison[f"{dataset_name}_std"] = np.std(strokes)
        
        comparison_results["stroke_count_comparison"] = stroke_comparison
        
        # Spatial correlation comparison
        comparison_results["spatial_correlation_comparison"] = analyze_spatial_correlation_comparison(
            custom_detailed, human_detailed, random_detailed
        )

        # Clustering comparison
        comparison_results["clustering_comparison"] = analyze_clustering_comparison(
            custom_detailed, human_detailed, random_detailed
        )
        
        # Temporal correlation comparison
        comparison_results["temporal_correlation_comparison"] = analyze_temporal_correlation_comparison(
            custom_detailed, human_detailed, random_detailed
        )
        
        # Hue entropy comparison (load separate image analysis results)
        custom_images, human_images, random_images = load_image_analysis_results(output_dir)
        
        hue_entropy_stats = {}
        
        # For custom: check both stroke results (old format) and separate image analysis (new format)
        if custom_detailed:
            custom_entropies = [r.get("hue_entropy") for r in custom_detailed if r.get("hue_entropy") is not None]
            if custom_entropies:
                hue_entropy_stats["custom"] = {
                    "mean": np.mean(custom_entropies),
                    "std": np.std(custom_entropies),
                    "count": len(custom_entropies)
                }
            elif custom_images:
                custom_entropies = [r.get("hue_entropy") for r in custom_images if r.get("hue_entropy") is not None]
                if custom_entropies:
                    hue_entropy_stats["custom"] = {
                        "mean": np.mean(custom_entropies),
                        "std": np.std(custom_entropies),
                        "count": len(custom_entropies)
                    }
        
        # For human: use separate image analysis
        if human_images:
            human_entropies = [r.get("hue_entropy") for r in human_images if r.get("hue_entropy") is not None]
            if human_entropies:
                hue_entropy_stats["human"] = {
                    "mean": np.mean(human_entropies),
                    "std": np.std(human_entropies),
                    "count": len(human_entropies)
                }
        
        # For random: use separate image analysis
        if random_images:
            random_entropies = [r.get("hue_entropy") for r in random_images if r.get("hue_entropy") is not None]
            if random_entropies:
                hue_entropy_stats["random"] = {
                    "mean": np.mean(random_entropies),
                    "std": np.std(random_entropies),
                    "count": len(random_entropies)
                }
        
        if hue_entropy_stats:
            comparison_results["hue_entropy_stats"] = hue_entropy_stats
    
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
    print(f"Random drawings: {datasets.get('random', {}).get('count', 0)} files")
    
    if "stroke_count_comparison" in comparison_results:
        stroke_stats = comparison_results["stroke_count_comparison"]
        print(f"\nStrokes per drawing:")
        if "custom_mean" in stroke_stats:
            print(f"  Custom AI: {stroke_stats['custom_mean']:.1f} ± {stroke_stats['custom_std']:.1f}")
        if "human_mean" in stroke_stats:
            print(f"  Human:     {stroke_stats['human_mean']:.1f} ± {stroke_stats['human_std']:.1f}")
        if "random_mean" in stroke_stats:
            print(f"  Random:    {stroke_stats['random_mean']:.1f} ± {stroke_stats['random_std']:.1f}")
    
    if "spatial_correlation_comparison" in comparison_results:
        spatial = comparison_results["spatial_correlation_comparison"]
        print(f"\nSpatial Correlation (Fréchet distances):")
        for dataset in ["custom", "human", "random"]:
            if not spatial.get(dataset, {}).get("no_data"):
                data = spatial[dataset]
                label = {"custom": "Custom AI", "human": "Human", "random": "Random"}[dataset]
                print(f"  {label:9}: {data['avg_mean_distance']:.1f} ± {data['std_mean_distance']:.1f} pixels")
                print(f"             ({data['total_color_pairs']} color pairs analyzed)")
    
    if "clustering_comparison" in comparison_results:
        clustering = comparison_results["clustering_comparison"]

        print(f"\nColor-based Spatial Clustering:")
        color_clust = clustering.get("color_clustering", {})
        for dataset in ["custom", "human", "random"]:
            if not color_clust.get(dataset, {}).get("no_data"):
                data = color_clust[dataset]
                label = {"custom": "Custom AI", "human": "Human", "random": "Random"}[dataset]
                print(f"  {label:9}: {data['avg_num_clusters']:.1f} ± {data['std_num_clusters']:.1f} clusters per color")
                print(f"             {data['avg_cluster_size']:.1f} ± {data['std_cluster_size']:.1f} strokes per cluster")
                if data['avg_intra_cluster_distance'] > 0:
                    print(f"             {data['avg_intra_cluster_distance']:.1f} ± {data['std_intra_cluster_distance']:.1f} pixels avg intra-cluster distance")
        
        print(f"\nBrush-based Spatial Clustering:")
        brush_clust = clustering.get("brush_clustering", {})
        for dataset in ["custom", "human", "random"]:
            if not brush_clust.get(dataset, {}).get("no_data"):
                data = brush_clust[dataset]
                label = {"custom": "Custom AI", "human": "Human", "random": "Random"}[dataset]
                print(f"  {label:9}: {data['avg_num_clusters']:.1f} ± {data['std_num_clusters']:.1f} clusters per brush")
                print(f"             {data['avg_cluster_size']:.1f} ± {data['std_cluster_size']:.1f} strokes per cluster")
                if data['avg_intra_cluster_distance'] > 0:
                    print(f"             {data['avg_intra_cluster_distance']:.1f} ± {data['std_intra_cluster_distance']:.1f} pixels avg intra-cluster distance")
    
    if "temporal_correlation_comparison" in comparison_results:
        temporal = comparison_results["temporal_correlation_comparison"]
        print(f"\nTemporal (Brush,Color) Correlation:")
        for dataset in ["custom", "human", "random"]:
            if not temporal.get(dataset, {}).get("no_data"):
                data = temporal[dataset]
                label = {"custom": "Custom AI", "human": "Human", "random": "Random"}[dataset]
                print(f"  {label:9}:")
                
                if "autocorrelation" in data:
                    autocorr = data["autocorrelation"]
                    print(f"             Autocorrelation: {autocorr['mean']:.3f} ± {autocorr['std']:.3f}")
                
                if "transition_entropy" in data:
                    entropy = data["transition_entropy"]
                    print(f"             Transition entropy: {entropy['mean']:.3f} ± {entropy['std']:.3f}")
                
                if "repetition_ratio" in data:
                    rep = data["repetition_ratio"]
                    print(f"             Repetition ratio: {rep['mean']:.3f} ± {rep['std']:.3f}")
                
                if "diversity" in data:
                    div = data["diversity"]
                    print(f"             Tool diversity: {div['mean']:.3f} ± {div['std']:.3f}")
    
    if "hue_entropy_stats" in comparison_results:
        entropy_stats = comparison_results["hue_entropy_stats"]
        print(f"\nHue Entropy (image analysis):")
        for dataset in ["custom", "human", "random"]:
            if dataset in entropy_stats:
                stats = entropy_stats[dataset]
                label = {"custom": "Custom AI", "human": "Human", "random": "Random"}[dataset]
                print(f"  {label:9}: {stats['mean']:.4f} ± {stats['std']:.4f} bits ({stats['count']} images)")
            else:
                label = {"custom": "Custom AI", "human": "Human", "random": "Random"}[dataset]
                if datasets.get(dataset, {}).get('count', 0) > 0:  # Only show if dataset exists
                    print(f"  {label:9}: No images found")

def main():
    """Main function to run eval-focused analysis."""
    output_dir = "../output/stats"
    
    # Run unified analysis script
    success = run_unified_analysis()
    
    if not success:
        print("Unified analysis failed. Exiting.")
        return

    # Load results
    custom_detailed, human_detailed, random_detailed = load_analysis_results(output_dir)
    
    if custom_detailed is None and human_detailed is None and random_detailed is None:
        print("No analysis results found. Exiting.")
        return

    # Create eval-focused comparative analysis
    comparison_results = create_eval_comparison(custom_detailed, human_detailed, random_detailed, output_dir)
    
    # Print summary
    print_eval_summary(comparison_results)

    print(f"\n=== Analysis Complete ===")
    print(f"All results saved in: {output_dir}")

if __name__ == "__main__":
    main()
