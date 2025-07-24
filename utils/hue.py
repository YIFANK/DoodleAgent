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

# Example usage
if __name__ == "__main__":
    # Load an example image
    image_path = "../output/20250723_191022/mood_angry.png"
    # image_path = "../test_final_result.png"
    image = Image.open(image_path).convert("RGB")
    rgb_np = np.array(image)

    entropy = compute_hue_entropy(rgb_np,bins = 36)
    print(f"Hue entropy: {entropy:.4f} bits")
