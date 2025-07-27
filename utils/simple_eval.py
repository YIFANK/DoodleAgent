#simple eval for the doodle agent

import cv2
import numpy as np
from PIL import Image

# ADD THIS COLOR GROUPING SECTION AT THE TOP
# ==================================================
# Color Grouping System
# ==================================================

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

# ==================================================
# Modified Analysis Functions
# ==================================================

def compute_hue_entropy(rgb_image: np.ndarray, bins: int = 36):
    """
    Compute the entropy of the hue distribution from an RGB image.

    Parameters:
        rgb_image (np.ndarray): Input image in RGB format (H, W, 3)
        bins (int): Number of bins for hue histogram (default 36 for 10-degree bins)

    Returns:
        float: Hue entropy (in bits)
    """
    print(rgb_image.shape)
    # Convert RGB to HSV
    hsv_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
    hue = hsv_image[:, :, 0]  # Hue channel (0 to 179 in OpenCV)

    # Normalize hue to 0-360 degrees
    hue_deg = hue.astype(np.float32) * 2  # [0, 360)

    # Compute histogram of hue
    hist, _ = np.histogram(hue_deg, bins=bins, range=(0, 360))

    # Normalize to probability distribution
    prob = hist / np.sum(hist)

    # Compute entropy
    entropy = -np.sum(prob * np.log2(prob + 1e-8))  # Add epsilon to avoid log(0)

    return entropy

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
    
    # Make curves same length by interpolating the shorter one
    if len(stroke1) > len(stroke2):
        # Interpolate stroke2 to match stroke1 length
        x = np.linspace(0, len(stroke2)-1, len(stroke1))
        xp = np.arange(len(stroke2))
        stroke2_interp = np.array([np.interp(x, xp, stroke2[:,i]) for i in range(stroke2.shape[1])]).T
        return frdist(stroke1, stroke2_interp)
    elif len(stroke2) > len(stroke1):
        # Interpolate stroke1 to match stroke2 length
        x = np.linspace(0, len(stroke1)-1, len(stroke2))
        xp = np.arange(len(stroke1))
        stroke1_interp = np.array([np.interp(x, xp, stroke1[:,i]) for i in range(stroke1.shape[1])]).T
        return frdist(stroke1_interp, stroke2)
    else:
        return frdist(stroke1, stroke2)

# MODIFIED FUNCTION: Now groups by color families instead of exact hex colors
def analyze_spatial_correlation(strokes):
    """Compute pairwise Fréchet distances between all strokes"""
    distances = []
    for s1, s2 in itertools.combinations(strokes, 2):
        d = compute_frechet_distance(s1, s2)
        distances.append(d)
    return np.mean(distances)

def stroke_centroid(stroke):
    x = np.array(stroke["stroke"]["x"])
    y = np.array(stroke["stroke"]["y"])
    return np.array([np.mean(x), np.mean(y)])

# MODIFIED FUNCTION: Now can group by color families for color-based clustering
def spatial_grouping_by(strokes, eps=50, min_samples=2, type="color"):
    """
    Group strokes by spatial proximity for each color group/brush.
    eps: max distance for clustering (in pixels)

    Returns detailed cluster information including average intra-cluster distances.
    """
    grouped = defaultdict(list)
    clusters_result = defaultdict(dict)
    
    # Step 1: group by color group or brush
    for stroke in strokes:
        if type == "color":
            # Use color group instead of exact color
            group_key = get_color_group(stroke["color"])
            grouped[group_key].append(stroke)
        elif type == "brush":
            grouped[stroke["brush"]].append(stroke)
        else:
            raise ValueError(f"Invalid type: {type}")
    
    # Calculate mean distance between strokes in each group, no clustering
    for group_key, strokes_list in grouped.items():
        distances = []
        if len(strokes_list) < 2:
            # Need at least 2 strokes to compute distances
            clusters_result[group_key]["mean_distance"] = 0.0
            clusters_result[group_key]["num_pairs"] = 0
            continue
            
        for s1, s2 in itertools.combinations(strokes_list, 2):
            try:
                d = compute_frechet_distance(s1, s2)
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
            
    return clusters_result

if __name__ == "__main__":
    # Test the functions
    strokes = [
        {"stroke": {"x": [0, 1, 2, 3, 4], "y": [0, 1, 2, 3, 4]}, "color": "#6BB9A4", "brush": "marker"},
        {"stroke": {"x": [5, 6, 7, 8, 9], "y": [5, 6, 7, 8, 9]}, "color": "#6BB9A4", "brush": "fountain"},
        {"stroke": {"x": [10, 11, 12, 13, 14], "y": [0, 1, 2, 3, 4]}, "color": "#7FC9E1", "brush": "marker"},
    ]
    print("Spatial correlation:", analyze_spatial_correlation(strokes))
    print("Color grouping:", spatial_grouping_by(strokes, type="color"))
    print("Brush grouping:", spatial_grouping_by(strokes, type="brush"))