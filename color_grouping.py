#!/usr/bin/env python3
"""
Color grouping utility to treat color variants within the same family as identical.
Add this to your analysis script or create as a separate utility module.
"""

# Define your color palette with groups
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
    """Normalize hex color format (ensure uppercase, with #)."""
    if not hex_color.startswith('#'):
        hex_color = '#' + hex_color
    return hex_color.upper()

def build_color_to_group_mapping():
    """Build a mapping from specific hex colors to their color group names."""
    color_to_group = {}

    for group_name, colors in COLOR_PALETTE.items():
        for shade_key, hex_color in colors.items():
            normalized_hex = normalize_hex_color(hex_color)
            color_to_group[normalized_hex] = group_name

    return color_to_group

def get_color_group(hex_color: str, color_mapping: dict = None) -> str:
    """
    Get the color group name for a given hex color.

    Args:
        hex_color: Hex color string (e.g., '#132822' or '132822')
        color_mapping: Pre-built mapping dict (optional, will build if None)

    Returns:
        Color group name (e.g., 'keppel') or the original hex if not found
    """
    if color_mapping is None:
        color_mapping = build_color_to_group_mapping()

    normalized_hex = normalize_hex_color(hex_color)
    return color_mapping.get(normalized_hex, normalized_hex)

def group_strokes_by_color_family(strokes_data: list, color_mapping: dict = None) -> dict:
    """
    Group strokes by color family instead of exact hex color.

    Args:
        strokes_data: List of stroke dictionaries with 'color' field
        color_mapping: Pre-built color mapping (optional)

    Returns:
        Dictionary mapping color group names to lists of strokes
    """
    if color_mapping is None:
        color_mapping = build_color_to_group_mapping()

    grouped_strokes = {}

    for stroke in strokes_data:
        original_color = stroke.get('color', '#000000')
        color_group = get_color_group(original_color, color_mapping)

        if color_group not in grouped_strokes:
            grouped_strokes[color_group] = []

        grouped_strokes[color_group].append(stroke)

    return grouped_strokes

# Integration functions for your existing analysis

def analyze_spatial_correlation_by_group(strokes_data: list, color_mapping: dict = None) -> dict:
    """
    Modified spatial correlation analysis using color groups.

    This replaces your existing spatial correlation logic.
    """
    from scipy.spatial.distance import cdist
    import numpy as np

    if color_mapping is None:
        color_mapping = build_color_to_group_mapping()

    grouped_strokes = group_strokes_by_color_family(strokes_data, color_mapping)
    spatial_correlation = {}

    for color_group, group_strokes in grouped_strokes.items():
        if len(group_strokes) < 2:
            continue

        # Extract stroke positions (assuming you have x, y coordinates)
        positions = []
        for stroke in group_strokes:
            # Adjust these field names based on your stroke data structure
            if 'x' in stroke and 'y' in stroke:
                positions.append([stroke['x'], stroke['y']])
            elif 'points' in stroke and stroke['points']:
                # If stroke has multiple points, use centroid
                points = stroke['points']
                avg_x = sum(p.get('x', 0) for p in points) / len(points)
                avg_y = sum(p.get('y', 0) for p in points) / len(points)
                positions.append([avg_x, avg_y])

        if len(positions) >= 2:
            positions = np.array(positions)
            # Calculate pairwise distances (Fréchet distance approximation)
            distances = cdist(positions, positions)

            # Get upper triangle (avoid duplicates and self-distances)
            upper_triangle = np.triu(distances, k=1)
            non_zero_distances = upper_triangle[upper_triangle > 0]

            if len(non_zero_distances) > 0:
                spatial_correlation[color_group] = {
                    "mean_distance": float(np.mean(non_zero_distances)),
                    "std_distance": float(np.std(non_zero_distances)),
                    "num_pairs": len(non_zero_distances),
                    "num_strokes": len(group_strokes)
                }

    return spatial_correlation

def analyze_clustering_by_group(strokes_data: list, color_mapping: dict = None, clustering_type: str = "color") -> dict:
    """
    Modified clustering analysis using color groups.

    Args:
        strokes_data: List of stroke data
        color_mapping: Color to group mapping
        clustering_type: "color" for color-based clustering, "brush" for brush-based
    """
    from sklearn.cluster import DBSCAN
    import numpy as np

    if color_mapping is None:
        color_mapping = build_color_to_group_mapping()

    if clustering_type == "color":
        grouped_strokes = group_strokes_by_color_family(strokes_data, color_mapping)
    else:  # brush-based clustering
        # Group by brush type instead
        grouped_strokes = {}
        for stroke in strokes_data:
            brush_type = stroke.get('brush', 'default')
            if brush_type not in grouped_strokes:
                grouped_strokes[brush_type] = []
            grouped_strokes[brush_type].append(stroke)

    clustering_results = {}

    for group_name, group_strokes in grouped_strokes.items():
        if len(group_strokes) < 2:
            continue

        # Extract positions for clustering
        positions = []
        for stroke in group_strokes:
            if 'x' in stroke and 'y' in stroke:
                positions.append([stroke['x'], stroke['y']])
            elif 'points' in stroke and stroke['points']:
                points = stroke['points']
                avg_x = sum(p.get('x', 0) for p in points) / len(points)
                avg_y = sum(p.get('y', 0) for p in points) / len(points)
                positions.append([avg_x, avg_y])

        if len(positions) >= 2:
            positions = np.array(positions)

            # Perform DBSCAN clustering
            clustering = DBSCAN(eps=50, min_samples=2).fit(positions)
            labels = clustering.labels_

            # Calculate cluster statistics
            unique_labels = set(labels)
            num_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)  # Exclude noise (-1)

            cluster_sizes = []
            intra_cluster_distances = []

            for label in unique_labels:
                if label == -1:  # Skip noise points
                    continue

                cluster_mask = labels == label
                cluster_positions = positions[cluster_mask]
                cluster_sizes.append(len(cluster_positions))

                # Calculate average intra-cluster distance
                if len(cluster_positions) > 1:
                    from scipy.spatial.distance import pdist
                    distances = pdist(cluster_positions)
                    intra_cluster_distances.extend(distances)

            clustering_results[group_name] = {
                "num_clusters": num_clusters,
                "cluster_sizes": cluster_sizes,
                "avg_cluster_size": np.mean(cluster_sizes) if cluster_sizes else 0,
                "avg_intra_cluster_distance": np.mean(intra_cluster_distances) if intra_cluster_distances else 0,
                "num_strokes": len(group_strokes)
            }

    return clustering_results

# Example usage and testing
def test_color_grouping():
    """Test the color grouping functionality."""
    test_colors = ['#132822', '#254F44', '#6BB9A4', '#0D2E39', '#7FC9E1']
    color_mapping = build_color_to_group_mapping()

    print("Color Grouping Test:")
    for color in test_colors:
        group = get_color_group(color, color_mapping)
        print(f"  {color} -> {group}")

    # Test with sample stroke data
    sample_strokes = [
        {'color': '#132822', 'x': 100, 'y': 150},
        {'color': '#254F44', 'x': 120, 'y': 160},
        {'color': '#6BB9A4', 'x': 110, 'y': 155},
        {'color': '#0D2E39', 'x': 300, 'y': 200},
        {'color': '#7FC9E1', 'x': 320, 'y': 210}
    ]

    grouped = group_strokes_by_color_family(sample_strokes, color_mapping)
    print(f"\nGrouped strokes:")
    for group, strokes in grouped.items():
        print(f"  {group}: {len(strokes)} strokes")

if __name__ == "__main__":
    test_color_grouping()
