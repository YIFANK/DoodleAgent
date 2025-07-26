import cv2
import numpy as np
from PIL import Image
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
    # print(s1.shape, s2.shape)
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

def analyze_spatial_correlation(strokes):
    """Group by color and compute pairwise Fréchet distances"""
    color_groups = defaultdict(list)

    for stroke in strokes:
        if "color" in stroke and "x" in stroke["stroke"] and "y" in stroke["stroke"]:
            centered = center_stroke(stroke)
            color_groups[stroke["color"]].append(centered)

    color_distances = {}

    for color, centered_strokes in color_groups.items():
        distances = []
        for s1, s2 in itertools.combinations(centered_strokes, 2):
            d = compute_frechet_distance(s1, s2)
            distances.append(d)
        color_distances[color] = distances

    return color_distances

from sklearn.cluster import DBSCAN
import numpy as np

def stroke_centroid(stroke):
    x = np.array(stroke["stroke"]["x"])
    y = np.array(stroke["stroke"]["y"])
    return np.array([np.mean(x), np.mean(y)])

def spatial_grouping_by(strokes, eps=50, min_samples=2,type = "color"):
    """
    Group strokes by spatial proximity for each color/brush.
    eps: max distance for clustering (in pixels)
    
    Returns detailed cluster information including average intra-cluster distances.
    """
    grouped = defaultdict(list)
    color_clusters = defaultdict(dict)

    # Step 1: group by color or brush
    for stroke in strokes:
        if type == "color":
            grouped[stroke["color"]].append(stroke)
        elif type == "brush":
            grouped[stroke["brush"]].append(stroke)
        else:
            raise ValueError(f"Invalid type: {type}")

    for color, strokes_list in grouped.items():
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
        
        color_clusters[color] = cluster_info

    return color_clusters
import json
# Example usage
if __name__ == "__main__":
    # Load an example image
    # image_path = "../output/20250723_191022/mood_angry.png"
    # # image_path = "../test_final_result.png"
    # image = Image.open(image_path).convert("RGB")
    # rgb_np = np.array(image)

    # entropy = compute_hue_entropy(rgb_np,bins = 36)
    # print(f"Hue entropy: {entropy:.4f} bits")
    stroke_path = "../humandoodle_test_10.json"
    with open(stroke_path, 'r') as f:
        human_strokes = json.load(f)

    spatial_correlation = analyze_spatial_correlation(human_strokes["strokes"])
    for color, distances in spatial_correlation.items():
         print(f"Color: {color}, Pairwise Fréchet distances: {distances}")

    color_clusters = spatial_grouping_by(human_strokes["strokes"],type = "color")
    for color, clusters in color_clusters.items():
        print(f"Color: {color}, Number of clusters: {len(clusters)}")
        for cluster_id, cluster_strokes in clusters.items():
            print(f"  Cluster {cluster_id}: {len(cluster_strokes)} strokes")

    brush_clusters = spatial_grouping_by(human_strokes["strokes"],type = "brush")
    
    