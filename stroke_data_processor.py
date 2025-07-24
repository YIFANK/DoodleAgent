#!/usr/bin/env python3
"""
Stroke Data Processor
===================

This script demonstrates how to load and process stroke data collected 
from the drawing canvas HTML interface.

The stroke data format is:
{
    "strokes": [
        {
            "x": [400, 450, 500, ...],
            "y": [250, 200, 275, ...]
        },
        ...
    ]
}
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_stroke_data(filepath):
    """Load stroke data from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def visualize_strokes(stroke_data, save_path=None):
    """Visualize all strokes in the data."""
    plt.figure(figsize=(12, 8))
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(stroke_data['strokes'])))
    
    for i, stroke in enumerate(stroke_data['strokes']):
        x_coords = stroke['x']
        y_coords = stroke['y']
        
        # Plot the stroke
        plt.plot(x_coords, y_coords, color=colors[i], linewidth=2, 
                marker='o', markersize=2, alpha=0.7, label=f'Stroke {i+1}')
    
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title(f'Human Drawing Strokes ({len(stroke_data["strokes"])} strokes)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    
    # Invert Y axis to match canvas coordinates (origin at top-left)
    plt.gca().invert_yaxis()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {save_path}")
    
    plt.show()


def analyze_strokes(stroke_data):
    """Analyze stroke characteristics."""
    strokes = stroke_data['strokes']
    
    print(f"=== Stroke Analysis ===")
    print(f"Total strokes: {len(strokes)}")
    
    if not strokes:
        print("No strokes to analyze.")
        return
    
    # Analyze each stroke
    stroke_lengths = []
    total_points = 0
    
    for i, stroke in enumerate(strokes):
        x_coords = np.array(stroke['x'])
        y_coords = np.array(stroke['y'])
        
        # Calculate stroke length
        if len(x_coords) > 1:
            distances = np.sqrt(np.diff(x_coords)**2 + np.diff(y_coords)**2)
            stroke_length = np.sum(distances)
            stroke_lengths.append(stroke_length)
        else:
            stroke_lengths.append(0)
        
        total_points += len(x_coords)
        
        print(f"Stroke {i+1}: {len(x_coords)} points, length: {stroke_lengths[-1]:.1f}px")
    
    print(f"\n=== Summary ===")
    print(f"Total points collected: {total_points}")
    print(f"Average points per stroke: {total_points/len(strokes):.1f}")
    print(f"Average stroke length: {np.mean(stroke_lengths):.1f}px")
    print(f"Longest stroke: {np.max(stroke_lengths):.1f}px")
    print(f"Shortest stroke: {np.min(stroke_lengths):.1f}px")


def convert_to_agent_format(stroke_data):
    """Convert stroke data to the format expected by drawing agents."""
    # This matches the format shown in free_drawing_agent.py
    converted = {
        "strokes": stroke_data['strokes']  # Already in the correct format
    }
    return converted


def main():
    """Main function to demonstrate usage."""
    # Look for stroke data files in the current directory
    stroke_files = list(Path('.').glob('strokes_*.json'))
    
    if not stroke_files:
        print("No stroke data files found.")
        print("Please draw something on the web interface and export the strokes.")
        return
    
    # Use the most recent file
    latest_file = max(stroke_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading stroke data from: {latest_file}")
    
    # Load and analyze the data
    stroke_data = load_stroke_data(latest_file)
    analyze_strokes(stroke_data)
    
    # Visualize the strokes
    vis_path = latest_file.stem + '_visualization.png'
    visualize_strokes(stroke_data, vis_path)
    
    # Convert to agent format (already in correct format)
    agent_format = convert_to_agent_format(stroke_data)
    agent_file = latest_file.stem + '_agent_format.json'
    
    with open(agent_file, 'w') as f:
        json.dump(agent_format, f, indent=2)
    
    print(f"Agent format saved to: {agent_file}")


if __name__ == "__main__":
    main() 