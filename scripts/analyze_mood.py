#!/usr/bin/env python3
"""
Analyze color usage across different moods in AI-generated drawing data.
Processes JSON files from happy, angry, and sad mood directories.
"""

import os
import json
import glob
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple
import matplotlib
matplotlib.use('Agg')  # Set backend for file saving without display
import matplotlib.pyplot as plt
import numpy as np

# Import necessary functions from other modules
from utils.simple_eval import get_color_group, COLOR_PALETTE
from unified_analysis import preprocess_json_to_stroke_format

def load_json_files(directory_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Load all JSON files from a directory.
    
    Args:
        directory_path: Path to directory containing JSON files
        
    Returns:
        List of tuples containing (filename, json_data)
    """
    json_files = []
    json_pattern = os.path.join(directory_path, "*.json")
    
    for file_path in glob.glob(json_pattern):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                filename = os.path.basename(file_path)
                json_files.append((filename, json_data))
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    return json_files

def analyze_color_usage_by_mood(mood_directories: Dict[str, str]) -> Dict[str, Dict[str, int]]:
    """
    Analyze color usage across different mood directories.
    
    Args:
        mood_directories: Dictionary mapping mood names to directory paths
        
    Returns:
        Dictionary mapping mood names to color usage counts
    """
    mood_color_analysis = {}
    
    for mood, directory_path in mood_directories.items():
        print(f"\nAnalyzing {mood} mood...")
        
        # Load all JSON files from the mood directory
        json_files = load_json_files(directory_path)
        print(f"Found {len(json_files)} JSON files for {mood} mood")
        
        # Initialize color counter for this mood
        color_counter = Counter()
        total_strokes = 0
        
        # Process each JSON file
        for filename, json_data in json_files:
            try:
                # Use custom format since these are AI-generated files
                strokes = preprocess_json_to_stroke_format(json_data, "custom")
                
                # Count strokes by color group
                for stroke in strokes:
                    color_group = get_color_group(stroke["color"])
                    color_counter[color_group] += 1
                    total_strokes += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        
        print(f"Total strokes processed for {mood}: {total_strokes}")
        mood_color_analysis[mood] = dict(color_counter)
    
    return mood_color_analysis

def get_top_colors(color_counts: Dict[str, int], top_n: int = 3) -> List[Tuple[str, int]]:
    """
    Get the top N colors by frequency.
    
    Args:
        color_counts: Dictionary of color counts
        top_n: Number of top colors to return
        
    Returns:
        List of tuples (color_name, count) sorted by count descending
    """
    return sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

def print_analysis_results(mood_color_analysis: Dict[str, Dict[str, int]]):
    """
    Print the analysis results in a formatted way.
    
    Args:
        mood_color_analysis: Results from analyze_color_usage_by_mood
    """
    print("\n" + "="*60)
    print("COLOR USAGE ANALYSIS BY MOOD")
    print("="*60)
    
    for mood, color_counts in mood_color_analysis.items():
        print(f"\n{mood.upper()} MOOD:")
        print("-" * 30)
        
        total_strokes = sum(color_counts.values())
        print(f"Total strokes: {total_strokes}")
        
        top_colors = get_top_colors(color_counts, 3)
        print("\nTop 3 colors:")
        
        for i, (color, count) in enumerate(top_colors, 1):
            percentage = (count / total_strokes * 100) if total_strokes > 0 else 0
            print(f"  {i}. {color}: {count} strokes ({percentage:.1f}%)")
        
        print(f"\nFull color distribution:")
        for color, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_strokes * 100) if total_strokes > 0 else 0
            print(f"  {color}: {count} strokes ({percentage:.1f}%)")

def create_visualizations(mood_color_analysis: Dict[str, Dict[str, int]]):
    """
    Create matplotlib visualizations for the color analysis.
    
    Args:
        mood_color_analysis: Results from analyze_color_usage_by_mood
    """
    # Create output directory if it doesn't exist
    os.makedirs("../visualize", exist_ok=True)
    
    # Check if we have data to visualize
    if not mood_color_analysis:
        print("No data to visualize!")
        return
    
    print(f"Creating visualizations for {len(mood_color_analysis)} moods...")
    for mood, counts in mood_color_analysis.items():
        print(f"  {mood}: {len(counts)} color groups, {sum(counts.values())} total strokes")

    # Get all unique colors across all moods
    all_colors = set()
    for color_counts in mood_color_analysis.values():
        all_colors.update(color_counts.keys())
    all_colors = sorted(list(all_colors))
    print(f"Found {len(all_colors)} unique color groups: {all_colors}")
    
    # Color mapping for visualization (use actual hex colors from palette)
    color_map = {}
    for color_name in all_colors:
        if color_name in COLOR_PALETTE:
            color_map[color_name] = COLOR_PALETTE[color_name]['DEFAULT']
        else:
            # For colors not in our palette, use a default color
            color_map[color_name] = '#808080'  # Gray
    
    # Create individual pie charts for each mood
    for mood, color_counts in mood_color_analysis.items():
        # Create individual figure for each mood
        fig_pie, ax_pie = plt.subplots(1, 1, figsize=(10, 8))
        
        # Get top colors for this mood
        top_colors = get_top_colors(color_counts, 8)  # Show more colors in pie chart
        
        if top_colors:
            colors = [color_map[color] for color, _ in top_colors]
            sizes = [count for _, count in top_colors]
            labels = [f'{color}\n({count})' for color, count in top_colors]
            
            wedges, texts, autotexts = ax_pie.pie(sizes, labels=labels, colors=colors, 
                                                 autopct='%1.1f%%', startangle=90)
            
            # Improve text readability
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
            
            for text in texts:
                text.set_fontsize(9)
            print(f"  Created pie chart for {mood} with {len(top_colors)} colors")
        else:
            ax_pie.text(0.5, 0.5, f'No data for {mood}', ha='center', va='center', transform=ax_pie.transAxes)
            print(f"  No data for {mood} mood")
            
        ax_pie.set_title(f'{mood.capitalize()} Mood - Color Usage Distribution', 
                        fontsize=14, fontweight='bold', pad=20)
        
        # Save individual pie chart
        try:
            save_path = f'../visualize/{mood}_mood_colors_pie.png'
            fig_pie.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved {mood} pie chart to {save_path}")
        except Exception as e:
            print(f"Error saving {mood} pie chart: {e}")
        finally:
            plt.close(fig_pie)
    
    # Create comparative bar chart as separate figure
    fig_bar, ax_bar = plt.subplots(1, 1, figsize=(12, 8))
    
    # Prepare data for grouped bar chart
    moods = list(mood_color_analysis.keys())
    colors_to_show = []
    
    # Get top 6 colors overall
    overall_color_counts = Counter()
    for color_counts in mood_color_analysis.values():
        for color, count in color_counts.items():
            overall_color_counts[color] += count
    
    colors_to_show = [color for color, _ in overall_color_counts.most_common(6)]
    print(f"Top colors to show in bar chart: {colors_to_show}")
    
    # Create grouped bar chart
    x = np.arange(len(colors_to_show))
    width = 0.25
    
    for i, mood in enumerate(moods):
        counts = [mood_color_analysis[mood].get(color, 0) for color in colors_to_show]
        bars = ax_bar.bar(x + i*width, counts, width, 
                         label=mood.capitalize(), alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax_bar.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    ax_bar.set_xlabel('Color Groups')
    ax_bar.set_ylabel('Number of Strokes')
    ax_bar.set_title('Color Usage Comparison Across Moods')
    ax_bar.set_xticks(x + width)
    ax_bar.set_xticklabels(colors_to_show, rotation=45, ha='right')
    ax_bar.legend()
    ax_bar.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the bar chart figure
    try:
        save_path = '../visualize/mood_color_comparison_bar.png'
        fig_bar.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved bar chart comparison to {save_path}")
    except Exception as e:
        print(f"Error saving bar chart: {e}")
    finally:
        plt.close(fig_bar)

    # Create a second figure for detailed top 3 colors visualization
    fig2, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Prepare data for top 3 colors comparison
    top3_data = {}
    for mood, color_counts in mood_color_analysis.items():
        top3_data[mood] = get_top_colors(color_counts, 3)
    
    # Create grouped bar chart for top 3 colors
    moods = list(top3_data.keys())
    x = np.arange(len(moods))
    width = 0.25
    
    # Get all unique top colors
    top_colors_set = set()
    for mood_top3 in top3_data.values():
        for color, _ in mood_top3:
            top_colors_set.add(color)
    
    top_colors_list = sorted(list(top_colors_set))
    
    for i, color in enumerate(top_colors_list):
        counts = []
        for mood in moods:
            # Find this color in the mood's top 3
            count = 0
            for c, cnt in top3_data[mood]:
                if c == color:
                    count = cnt
                    break
            counts.append(count)
        
        bars = ax.bar(x + i*width - (len(top_colors_list)-1)*width/2, counts, width,
                     label=color, color=color_map[color], alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Moods')
    ax.set_ylabel('Number of Strokes')
    ax.set_title('Top Colors Distribution Across Different Moods')
    ax.set_xticks(x)
    ax.set_xticklabels([mood.capitalize() for mood in moods])
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the second figure
    try:
        save_path = '../visualize/top_colors_by_mood.png'
        fig2.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")
    except Exception as e:
        print(f"Error saving second visualization: {e}")
    finally:
        plt.close(fig2)

def main():
    """
    Main function to run the color usage analysis.
    """
    # Define mood directories
    base_path = "../mood"  # Relative to DoodleAgent directory
    mood_directories = {
        "happy": os.path.join(base_path, "happy", "json"),
        "angry": os.path.join(base_path, "angry", "json"),
        "sad": os.path.join(base_path, "sad", "json")
    }
    
    # Check if directories exist and have files
    for mood, path in mood_directories.items():
        if not os.path.exists(path):
            print(f"Error: Directory {path} does not exist")
            return
        json_files = glob.glob(os.path.join(path, "*.json"))
        print(f"Found {len(json_files)} JSON files in {path}")
        if len(json_files) == 0:
            print(f"Warning: No JSON files found in {path}")
    
    print("Starting color usage analysis across mood-based drawings...")
    
    # Analyze color usage
    mood_color_analysis = analyze_color_usage_by_mood(mood_directories)
    
    # Print results
    print_analysis_results(mood_color_analysis)
    
        # Create visualizations
    print("\nGenerating visualizations...")
    create_visualizations(mood_color_analysis)
    
    print("\nAnalysis complete!")
    print("Generated files:")
    print("  - Individual pie charts for each mood: happy_mood_colors_pie.png, angry_mood_colors_pie.png, sad_mood_colors_pie.png")
    print("  - Color comparison bar chart: mood_color_comparison_bar.png")
    print("  - Top 3 colors detailed comparison: top_colors_by_mood.png")
    print("All files saved to '../visualize/' directory")

if __name__ == "__main__":
    main()
