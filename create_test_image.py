#!/usr/bin/env python3
"""
Simple script to create a test image for the painting imitation demo.
Creates a simple geometric pattern that the agent can try to imitate.
"""

from PIL import Image, ImageDraw
import os

def create_test_image():
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a 800x600 image with a white background
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a simple geometric pattern
    # Background gradient
    for y in range(height):
        color = int(255 * (1 - y / height))
        draw.line([(0, y), (width, y)], fill=(color, color, 255))
    
    # Draw a red circle in the center
    center_x, center_y = width // 2, height // 2
    circle_radius = 80
    draw.ellipse([
        center_x - circle_radius, 
        center_y - circle_radius,
        center_x + circle_radius, 
        center_y + circle_radius
    ], fill='red', outline='darkred', width=3)
    
    # Draw a green triangle
    triangle_points = [
        (center_x - 100, center_y + 120),
        (center_x + 100, center_y + 120),
        (center_x, center_y + 200)
    ]
    draw.polygon(triangle_points, fill='green', outline='darkgreen', width=2)
    
    # Draw some blue rectangles
    draw.rectangle([50, 50, 150, 100], fill='blue', outline='darkblue', width=2)
    draw.rectangle([600, 450, 700, 500], fill='blue', outline='darkblue', width=2)
    
    # Draw yellow lines
    draw.line([(200, 100), (300, 200)], fill='yellow', width=5)
    draw.line([(500, 400), (600, 300)], fill='yellow', width=5)
    
    # Save the image
    output_path = os.path.join(output_dir, "test_imitation_target.png")
    image.save(output_path)
    print(f"✅ Test image created: {output_path}")
    print(f"   Size: {width}x{height} pixels")
    print(f"   Features: gradient background, red circle, green triangle, blue rectangles, yellow lines")
    
    return output_path

if __name__ == "__main__":
    create_test_image() 