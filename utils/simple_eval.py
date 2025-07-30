#simple eval for the doodle agent

import cv2
import numpy as np
from PIL import Image

# ADD THIS COLOR GROUPING SECTION AT THE TOP
# ==================================================
# Color Grouping System
# ==================================================
from Fred import discrete_frechet
import Fred as fred
COLOR_PALETTE = {
    'keppel': {
        'DEFAULT': '#6BB9A4',
        '100': '#132822',
        '200': '#254F44',
        '300': '#387766',
        '400': '#4A9E88',
        '500': '#6BB9A4',
        '600': '#88C7B6',
        '700': '#A6D5C8',
        '800': '#C3E3DB',
        '900': '#E1F1ED'
    },
    'sky_blue': {
        'DEFAULT': '#7FC9E1',
        '100': '#0D2E39',
        '200': '#1B5C72',
        '300': '#288AAB',
        '400': '#46B0D4',
        '500': '#7FC9E1',
        '600': '#99D3E7',
        '700': '#B2DEED',
        '800': '#CCE9F3',
        '900': '#E5F4F9'
    },
    'tea_rose_(red)': {
        'DEFAULT': '#FFD1D1',
        '100': '#5D0000',
        '200': '#BA0000',
        '300': '#FF1717',
        '400': '#FF7474',
        '500': '#FFD1D1',
        '600': '#FFDADA',
        '700': '#FFE3E3',
        '800': '#FFEDED',
        '900': '#FFF6F6'
    },
    'light_red': {
        'DEFAULT': '#FF7878',
        '100': '#4B0000',
        '200': '#970000',
        '300': '#E20000',
        '400': '#FF2F2F',
        '500': '#FF7878',
        '600': '#FF9595',
        '700': '#FFAFAF',
        '800': '#FFCACA',
        '900': '#FFE4E4'
    },
    'jasmine': {
        'DEFAULT': '#FFE978',
        '100': '#4B3F00',
        '200': '#977E00',
        '300': '#E2BD00',
        '400': '#FFDC2F',
        '500': '#FFE978',
        '600': '#FFED95',
        '700': '#FFF2AF',
        '800': '#FFF6CA',
        '900': '#FFFBE4'
    },
    'wisteria': {
        'DEFAULT': '#CF94EE',
        '100': '#2F0A43',
        '200': '#5E1586',
        '300': '#8E1FC9',
        '400': '#B152E4',
        '500': '#CF94EE',
        '600': '#D9AAF2',
        '700': '#E2BFF5',
        '800': '#ECD5F8',
        '900': '#F5EAFC'
    }
}

def normalize_hex_color(hex_color: str) -> str:
    """Normalize hex color format."""
    if not hex_color.startswith('#'):
        hex_color = '#' + hex_color
    return hex_color.upper()

def build_color_to_group_mapping():
    """Build mapping from hex colors to color group names."""
    color_to_group = {}
    for group_name, colors in COLOR_PALETTE.items():
        for shade_key, hex_color in colors.items():
            normalized_hex = normalize_hex_color(hex_color)
            color_to_group[normalized_hex] = group_name
    return color_to_group

def get_color_group(hex_color: str) -> str:
    """Get color group name for a hex color."""
    color_mapping = build_color_to_group_mapping()
    normalized_hex = normalize_hex_color(hex_color)
    return color_mapping.get(normalized_hex, normalized_hex)

def compute_stroke_statistics(strokes):
    """
    Calculate min/max/mean/std statistics for all stroke coordinates.
    
    Args:
        strokes: List of stroke dictionaries with format:
                {"stroke": {"x": [...], "y": [...]}, "color": "...", "brush": "..."}
    
    Returns:
        dict: Statistics containing bounding box and coordinate statistics
    """
    if not strokes:
        return {}
    
    # Collect all x and y coordinates
    all_x = []
    all_y = []
    
    for stroke in strokes:
        x_coords = stroke["stroke"]["x"]
        y_coords = stroke["stroke"]["y"]
        all_x.extend(x_coords)
        all_y.extend(y_coords)
    
    all_x = np.array(all_x)
    all_y = np.array(all_y)
    
    statistics = {
        "x_stats": {
            "min": float(np.min(all_x)),
            "max": float(np.max(all_x)),
            "mean": float(np.mean(all_x)),
            "std": float(np.std(all_x))
        },
        "y_stats": {
            "min": float(np.min(all_y)),
            "max": float(np.max(all_y)),
            "mean": float(np.mean(all_y)),
            "std": float(np.std(all_y))
        },
        "bounding_box": {
            "x_min": float(np.min(all_x)),
            "x_max": float(np.max(all_x)),
            "y_min": float(np.min(all_y)),
            "y_max": float(np.max(all_y)),
            "width": float(np.max(all_x) - np.min(all_x)),
            "height": float(np.max(all_y) - np.min(all_y))
        },
        "total_points": len(all_x)
    }
    
    return statistics

def normalize_strokes(strokes):
    """
    Normalize stroke coordinates to [0,1] range based on bounding rectangle.
    
    Args:
        strokes: List of stroke dictionaries
        
    Returns:
        List of normalized stroke dictionaries with same structure
    """
    if not strokes:
        return strokes
    
    # # Get bounding box statistics
    # stats = compute_stroke_statistics(strokes)
    # bbox = stats["bounding_box"]
    #get the max bounding box for a single stroke
    # Get min/max x and y coordinates across all strokes
    x_min = float('inf')
    x_max = float('-inf')
    y_min = float('inf')
    y_max = float('-inf')
    width = 1e-6
    height = 1e-6
    for stroke in strokes:
        x_coords = stroke["stroke"]["x"]
        y_coords = stroke["stroke"]["y"]
        x_min = min(x_min, min(x_coords))
        x_max = max(x_max, max(x_coords))
        y_min = min(y_min, min(y_coords))
        y_max = max(y_max, max(y_coords))
        width = max(width,x_max - x_min)
        height = max(height,y_max - y_min)

    
    normalized_strokes = []
    
    for stroke in strokes:
        # Normalize coordinates
        x_coords = np.array(stroke["stroke"]["x"])
        y_coords = np.array(stroke["stroke"]["y"])
        
        # Normalize so that each stroke is bounded in unit square
        normalized_x = x_coords / width
        normalized_y = y_coords / height
        
        # Create normalized stroke dictionary
        normalized_stroke = {
            "color": stroke["color"],
            "brush": stroke["brush"],
            "stroke": {
                "x": normalized_x.tolist(),
                "y": normalized_y.tolist()
            }
        }
        
        normalized_strokes.append(normalized_stroke)
    
    return normalized_strokes

#calculate spatial correlation using frechet distance
from frechetdist import frdist
import numpy as np
from collections import defaultdict
import itertools

def center_stroke(stroke):
    """Shift stroke to center around (0,0)"""
    x = np.array(stroke["stroke"]["x"])
    y = np.array(stroke["stroke"]["y"])
    center_x = np.mean(x)
    center_y = np.mean(y)
    centered = np.stack([x - center_x, y - center_y], axis=1)
    return centered
def compute_frechet_distance(s1, s2):
    """Compute discrete Fréchet distance between two strokes (2D curves)"""
    # Extract coordinate arrays from stroke dictionaries
    x1 = np.array(s1["stroke"]["x"])
    y1 = np.array(s1["stroke"]["y"])
    stroke1 = np.stack([x1, y1], axis=1)
    
    x2 = np.array(s2["stroke"]["x"])
    y2 = np.array(s2["stroke"]["y"])
    stroke2 = np.stack([x2, y2], axis=1)
    #center the strokes
    stroke1 = stroke1 - stroke_centroid(s1)
    stroke2 = stroke2 - stroke_centroid(s2)
    # print(stroke1,stroke2)
    #convert to fred.curve
    curve1 = fred.Curve(stroke1) 
    curve2 = fred.Curve(stroke2)
    d = discrete_frechet(curve1, curve2).value
    return d
# MODIFIED FUNCTION: Now groups by color families instead of exact hex colors
def analyze_spatial_correlation(strokes, normalize=True):
    """Compute pairwise Fréchet distances between all strokes"""
    if len(strokes) < 2:
        return 0.0
    
    # Optionally normalize strokes first for consistent comparison
    if normalize:
        analysis_strokes = normalize_strokes(strokes)
    else:
        analysis_strokes = strokes
    
    distances = []
    for s1, s2 in itertools.combinations(analysis_strokes, 2):
        d = compute_frechet_distance(s1, s2)
        distances.append(d)
    return np.mean(distances)

def stroke_centroid(stroke):
    x = np.array(stroke["stroke"]["x"])
    y = np.array(stroke["stroke"]["y"])
    return np.array([np.mean(x), np.mean(y)])

# MODIFIED FUNCTION: Now can group by color families for color-based clustering
def spatial_grouping_by(strokes, type="color", normalize=True):
    """
    Group strokes by spatial proximity for each color group/brush.
    eps: max distance for clustering (in pixels)

    Returns detailed cluster information including average intra-cluster distances.
    """
    grouped = defaultdict(list)
    clusters_result = defaultdict(dict)
    
    # Optionally normalize strokes first for consistent comparison
    if normalize:
        analysis_strokes = normalize_strokes(strokes)
    else:
        analysis_strokes = strokes
    
    # Step 1: group by color group or brush
    for stroke in analysis_strokes:
        if type == "color":
            # Use color group instead of exact color
            group_key = get_color_group(stroke["color"])
            grouped[group_key].append(stroke)
        elif type == "brush":
            grouped[stroke["brush"]].append(stroke)
        elif type =="brush_color":
            #group by brush and color
            group_key = f"{stroke['brush']}_{get_color_group(stroke['color'])}"
            grouped[group_key].append(stroke)
        else:
            raise ValueError(f"Invalid type: {type}")
    #count the number of different colors and brushes
    return grouped
def color_count(strokes):
    return len(set([stroke["color"] for stroke in strokes]))
def brush_count(strokes):
    return len(set([stroke["brush"] for stroke in strokes]))
def brush_color_count(strokes):
    return len(set([f"{stroke['brush']}_{get_color_group(stroke['color'])}" for stroke in strokes]))

def analyze_type_metrics(strokes, type="color", metric="frechet", normalize=True):
    """
    Calculate mean distance between strokes in each group, no clustering.
    
    Args:
        strokes: List of stroke dictionaries
        type: "color" or "brush" for grouping type
        metric: "frechet" or "euclidean" for distance calculation
        normalize: Whether to normalize strokes first
        
    Returns:
        Dictionary with group analysis results
    """
    # Initialize results dictionary
    clusters_result = defaultdict(dict)
    
    # First group by type (color or brush)
    grouped = spatial_grouping_by(strokes, type=type, normalize=normalize)
    
    # Calculate mean distance between strokes in each group
    for group_key, strokes_list in grouped.items():
        distances = []
        if len(strokes_list) < 2:
            # Need at least 2 strokes to compute distances
            clusters_result[group_key]["mean_distance"] = 0.0
            clusters_result[group_key]["num_pairs"] = 0
            continue
            
        for s1, s2 in itertools.combinations(strokes_list, 2):
            try:
                if metric == "frechet":
                    d = compute_frechet_distance(s1, s2)
                elif metric == "euclidean":
                    d = compute_euclidean_distance(s1, s2)
                else:
                    raise ValueError(f"Invalid metric: {metric}")
                distances.append(d)
            except Exception as e:
                print(f"Error computing distance for group {group_key}: {e}")
                continue
                
        if distances:
            clusters_result[group_key]["mean_distance"] = np.mean(distances)
            clusters_result[group_key]["num_pairs"] = len(distances)
        else:
            clusters_result[group_key]["mean_distance"] = 0.0
            clusters_result[group_key]["num_pairs"] = 0
            
    return dict(clusters_result)

def compute_euclidean_distance(s1, s2):
    """Compute Euclidean distance between two strokes' centroids"""
    x1 = np.array(s1["stroke"]["x"])
    y1 = np.array(s1["stroke"]["y"])
    x2 = np.array(s2["stroke"]["x"])
    y2 = np.array(s2["stroke"]["y"])
    centroid1 = np.array([np.mean(x1), np.mean(y1)])
    centroid2 = np.array([np.mean(x2), np.mean(y2)])
    d = np.linalg.norm(centroid1 - centroid2)
    return d

def if_same_color(s1, s2):
    s1_color_group = get_color_group(s1["color"])
    s2_color_group = get_color_group(s2["color"])
    return s1_color_group == s2_color_group

def if_same_brush(s1, s2):
    return s1["brush"] == s2["brush"]

def if_same_color_and_brush(s1, s2):
    #use the color group instead of the exact color
    return if_same_color(s1, s2) and if_same_brush(s1, s2)

def compute_temporal_correlation(strokes, type="color_and_brush"):
    """Compute temporal correlation between strokes"""
    if len(strokes) < 2:
        return 0.0
    count = 0
    for i in range(len(strokes) - 1):
        if type == "color_and_brush":
            if if_same_color_and_brush(strokes[i], strokes[i+1]):
                count += 1
        elif type == "color":
            if if_same_color(strokes[i], strokes[i+1]):
                count += 1
        elif type == "brush":
            if if_same_brush(strokes[i], strokes[i+1]):
                count += 1
        else:
            raise ValueError(f"Invalid type: {type}")
    return count / (len(strokes) - 1)
def compute_smoothness(stroke):
    """Compute smoothness of a stroke by calculating the angle between consecutive edges"""
    angles = []
    edges = []
    for i in range(len(stroke["stroke"]["x"]) - 1):
        edge = (stroke["stroke"]["x"][i+1] - stroke["stroke"]["x"][i], stroke["stroke"]["y"][i+1] - stroke["stroke"]["y"][i])
        edges.append(edge)
    for i in range(len(edges) - 1):
        angle = np.dot(edges[i], edges[i+1]) / (np.linalg.norm(edges[i]) * np.linalg.norm(edges[i+1]))
        angles.append(angle)
    return np.mean(angles)
if __name__ == "__main__":
    # Test the functions
    strokes = [
        {"stroke": {"x": [0, 1, 2, 3, 4], "y": [0, 1, 2, 3, 4]}, "color": "#6BB9A4", "brush": "marker"},
        {"stroke": {"x": [50, 60, 70, 80, 90], "y": [100, 110, 120, 130, 140]}, "color": "#6BB9A4", "brush": "fountain"},
        {"stroke": {"x": [200, 210, 220, 230, 240], "y": [10, 20, 30, 40, 50]}, "color": "#7FC9E1", "brush": "marker"},
    ]
    
    print("=== Original Stroke Statistics ===")
    stats = compute_stroke_statistics(strokes)
    print("Stroke statistics:", stats)
    
    print("\n=== Normalized Strokes ===")
    normalized = normalize_strokes(strokes)
    normalized_stats = compute_stroke_statistics(normalized)
    print("Normalized statistics:", normalized_stats)
    
    print("\n=== Analysis Results (Normalized) ===")
    print("Spatial correlation:", analyze_spatial_correlation(strokes, normalize=True))
    print("Color grouping:", spatial_grouping_by(strokes, type="color", normalize=True))
    print("Brush grouping:", spatial_grouping_by(strokes, type="brush", normalize=True))
    
    print("\n=== Analysis Results (Raw/Unnormalized) ===")
    print("Spatial correlation:", analyze_spatial_correlation(strokes, normalize=False))
    print("Color grouping:", spatial_grouping_by(strokes, type="color", normalize=False))
    print("Brush grouping:", spatial_grouping_by(strokes, type="brush", normalize=False))