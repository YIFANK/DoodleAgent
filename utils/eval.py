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
    # Make curves same length by interpolating the shorter one
    if len(s1) > len(s2):
        # Interpolate s2 to match s1 length
        x = np.linspace(0, len(s2)-1, len(s1))
        xp = np.arange(len(s2))
        s2_interp = np.array([np.interp(x, xp, s2[:,i]) for i in range(s2.shape[1])]).T
        return frdist(s1, s2_interp)
    elif len(s2) > len(s1):
        # Interpolate s1 to match s2 length
        x = np.linspace(0, len(s1)-1, len(s2))
        xp = np.arange(len(s1))
        s1_interp = np.array([np.interp(x, xp, s1[:,i]) for i in range(s1.shape[1])]).T
        return frdist(s1_interp, s2)
    else:
        return frdist(s1, s2)

# MODIFIED FUNCTION: Now groups by color families instead of exact hex colors
def analyze_spatial_correlation(strokes):
    """Group by color groups (not exact colors) and compute pairwise Fréchet distances"""
    color_groups = defaultdict(list)

    for stroke in strokes:
        if "color" in stroke and "x" in stroke["stroke"] and "y" in stroke["stroke"]:
            # Get color group instead of exact hex color
            color_group = get_color_group(stroke["color"])
            centered = center_stroke(stroke)
            color_groups[color_group].append(centered)

    color_distances = {}

    for color_group, centered_strokes in color_groups.items():
        distances = []
        for s1, s2 in itertools.combinations(centered_strokes, 2):
            d = compute_frechet_distance(s1, s2)
            distances.append(d)
        color_distances[color_group] = distances

    return color_distances

from sklearn.cluster import DBSCAN
import numpy as np

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

    for group_key, strokes_list in grouped.items():
        # Step 2: compute centroids
        centroids = np.array([stroke_centroid(stroke) for stroke in strokes_list])

        # Step 3: cluster using DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centroids)
        labels = clustering.labels_

        # Step 4: group strokes by cluster label and calculate intra-cluster distances
        cluster_map = defaultdict(list)
        cluster_centroids = defaultdict(list)

        for idx, label in enumerate(labels):
            cluster_map[label].append(strokes_list[idx])
            cluster_centroids[label].append(centroids[idx])

        # Step 5: calculate average intra-cluster distances
        cluster_info = {}
        for cluster_id, cluster_strokes in cluster_map.items():
            cluster_centroid_points = np.array(cluster_centroids[cluster_id])

            # Calculate average distance between all pairs of centroids in this cluster
            if len(cluster_centroid_points) > 1:
                distances = []
                for i in range(len(cluster_centroid_points)):
                    for j in range(i + 1, len(cluster_centroid_points)):
                        # Euclidean distance between centroids
                        dist = np.sqrt(np.sum((cluster_centroid_points[i] - cluster_centroid_points[j])**2))
                        distances.append(dist)
                avg_intra_cluster_distance = np.mean(distances) if distances else 0.0
            else:
                avg_intra_cluster_distance = 0.0  # Single stroke cluster has no internal distance

            cluster_info[cluster_id] = {
                "strokes": cluster_strokes,
                "num_strokes": len(cluster_strokes),
                "avg_intra_cluster_distance": float(avg_intra_cluster_distance),
                "cluster_centroid": np.mean(cluster_centroid_points, axis=0).tolist() if len(cluster_centroid_points) > 0 else [0, 0]
            }

        clusters_result[group_key] = cluster_info

    return clusters_result

import json

# Example usage with debugging
if __name__ == "__main__":
    stroke_path = "../humandoodle_test_10.json"
    with open(stroke_path, 'r') as f:
        human_strokes = json.load(f)

    print("=== Testing Color Grouping ===")
    # Test color grouping with sample colors
    test_colors = ['#132822', '#254F44', '#6BB9A4', '#0D2E39', '#7FC9E1']
    for color in test_colors:
        group = get_color_group(color)
        print(f"{color} -> {group}")

    print("\n=== Spatial Correlation Analysis (with color grouping) ===")
    spatial_correlation = analyze_spatial_correlation(human_strokes["strokes"])
    for color_group, distances in spatial_correlation.items():
        print(f"Color group: {color_group}, Pairwise Fréchet distances: {len(distances)} pairs")
        if distances:
            print(f"  Mean distance: {np.mean(distances):.2f}, Std: {np.std(distances):.2f}")

    print("\n=== Color Group Clustering ===")
    color_clusters = spatial_grouping_by(human_strokes["strokes"], type="color")
    for color_group, clusters in color_clusters.items():
        print(f"Color group: {color_group}, Number of clusters: {len(clusters)}")
        for cluster_id, cluster_info in clusters.items():
            print(f"  Cluster {cluster_id}: {cluster_info['num_strokes']} strokes, avg distance: {cluster_info['avg_intra_cluster_distance']:.2f}")

    print("\n=== Brush Clustering (unchanged) ===")
    brush_clusters = spatial_grouping_by(human_strokes["strokes"], type="brush")
    for brush, clusters in brush_clusters.items():
        print(f"Brush: {brush}, Number of clusters: {len(clusters)}")
