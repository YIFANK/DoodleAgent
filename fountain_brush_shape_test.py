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

output_dir = "fountain_shape_test_results"
os.makedirs(output_dir, exist_ok=True)

bridge = DrawingCanvasBridge()
bridge.start_canvas_interface()

def draw_fountain_stroke_js(bridge, x_coords, y_coords, step_length, step_duration):
    js_code = f'''
    const x_coords = {x_coords};
    const y_coords = {y_coords};
    const steps_per_segment = Math.max(2, Math.floor({step_length}) || 2);
    function lerp(a, b, t) {{ return a + (b - a) * t; }}
    for (let i = 0; i < x_coords.length - 1; i++) {{
        const startX = x_coords[i];
        const startY = y_coords[i];
        const endX = x_coords[i+1];
        const endY = y_coords[i+1];
        for (let s = 0; s <= steps_per_segment; s++) {{
            const t = s / steps_per_segment;
            const interpX = lerp(startX, endX, t);
            const interpY = lerp(startY, endY, t);
            window.pmouseX = (s === 0) ? startX : window.mouseX;
            window.pmouseY = (s === 0) ? startY : window.mouseY;
            window.mouseX = interpX;
            window.mouseY = interpY;
            window['fountainPen']();
        }}
        if ({step_duration} > 0) {{
            const start = Date.now();
            while (Date.now() - start < {step_duration}) {{}}
        }}
    }}
    '''
    bridge.driver.execute_script(js_code)

try:
    for i in range(10):
        step_length = step_lengths[i]
        step_duration = step_durations[i]
        bridge.clear_canvas()
        bridge.set_brush("fountain")
        for shape, x_offset in zip(shapes, x_offsets):
            # Offset the shape horizontally and vertically
            x = [xi + x_offset for xi in shape["x"]]
            y = [yi + y_offset for yi in shape["y"]]
            draw_fountain_stroke_js(bridge, x, y, step_length, step_duration)
        time.sleep(1.2)
        filename = f"{output_dir}/fountain_allshapes_len{step_length}_dur{step_duration}.png"
        bridge.capture_canvas(filename)
        print(f"Saved: {filename}")
finally:
    bridge.close()
