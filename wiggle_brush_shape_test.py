import os
import time
from drawing_canvas_bridge import DrawingCanvasBridge

# Define the shapes (base positions)
shapes = [
    {
        "name": "vertical_line",
        "x": [0, 0],
        "y": [0, 150]
    },
    {
        "name": "horizontal_line",
        "x": [0, 200],  # Make horizontal line longer
        "y": [0, 0]
    },
    {
        "name": "u_curve",
        "x": [0, 50, 100, 150, 200],
        "y": [100, 90, 80, 90, 100]
    },
    {
        "name": "n_curve",
        "x": [0, 50, 100, 150, 200],
        "y": [80, 90, 100, 90, 80]
    }
]

# Offsets for each shape (so they appear side by side)
x_offsets = [100, 300, 500, 700]
y_offset = 150

step_lengths = [i * 4 for i in range(10)]      # 0, 4, 8, ..., 36
step_durations = [i * 10 for i in range(10)]   # 0, 10, 20, ..., 90

output_dir = "wiggle_shape_test_results"
os.makedirs(output_dir, exist_ok=True)

bridge = DrawingCanvasBridge()
bridge.start_canvas_interface() 

def draw_stroke_js(bridge, x_coords, y_coords, step_length, step_duration, brush_type):
    bridge._execute_continuous_stroke(x_coords,y_coords,step_length,step_duration,brush_type)

def test_draw(step_lengths, step_durations, brush_type):
    for i in range(1,10):
        step_length = step_lengths[i]
        step_duration = step_durations[i]
        bridge.clear_canvas()
        for shape, x_offset in zip(shapes, x_offsets):
            # Offset the shape horizontally and vertically
            x = [xi + x_offset for xi in shape["x"]]
            y = [yi + y_offset for yi in shape["y"]]
            draw_stroke_js(bridge, x, y, step_length, step_duration, brush_type)
            # time.sleep(3)
        time.sleep(1.2)
        filename = f"{output_dir}/{brush_type}_allshapes_len{step_length}_dur{step_duration}.png"
        bridge.capture_canvas(filename)
        print(f"Saved: {filename}")

if __name__ == "__main__":
    test_draw(step_lengths, step_durations, "crayon")
    # test_draw(step_lengths, step_durations, "fountainPen")
    # test_draw(step_lengths, step_durations, "marker")
    # test_draw(step_lengths, step_durations, "pen")
    # test_draw(step_lengths, step_durations, "sprayPaint")
    # test_draw(step_lengths, step_durations, "wiggle")
