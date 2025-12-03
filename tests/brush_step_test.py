import os
import time
from drawing_canvas_bridge import DrawingCanvasBridge

# Parameter grid
step_lengths = [i * 4 for i in range(11)]      # 0, 4, 8, ..., 40
step_durations = [i * 10 for i in range(11)]   # 0, 10, 20, ..., 100
brushes = ["marker", "wiggle", "fountain"]

output_dir = "brush_step_test_results"
os.makedirs(output_dir, exist_ok=True)

# Initialize the bridge
bridge = DrawingCanvasBridge()
bridge.start_canvas_interface()

try:
    for brush in brushes:
        for step_length in step_lengths:
            for step_duration in step_durations:
                # Clear canvas before each test
                bridge.clear_canvas()
                bridge.set_brush(brush)
                # Draw a simple horizontal line
                x_coords = [100, 300]
                y_coords = [200, 200]
                bridge._execute_continuous_stroke(x_coords, y_coords, step_length=step_length, step_duration=step_duration)
                # Wait for the stroke to finish (adjust as needed)
                time.sleep(1.2)
                # Capture the result
                filename = f"{output_dir}/{brush}_len{step_length}_dur{step_duration}.png"
                bridge.capture_canvas(filename)
                print(f"Saved: {filename}")
finally:
    bridge.close()
