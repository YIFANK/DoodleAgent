#!/usr/bin/env python3
"""
Generate MP4 video from drawing agent session logs - LITE VERSION (no OpenCV).
This script replays the drawing session step by step and creates videos using imageio.
Now captures frames DURING the drawing process for real-time stroke visualization.
"""

import os
import json
import re
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from free_drawing_agent import DrawingInstruction
import base64
from dotenv import load_dotenv
import threading

load_dotenv()

class DrawingCanvasBridgeVideoCapture:
    """
    Extended bridge that captures frames during drawing for video generation.
    """

    def __init__(self, canvas_url: str = None):
        self.canvas_url = canvas_url or f"file://{os.path.abspath('drawing_canvas.html')}"
        self.driver = None
        self.canvas = None
        self.wait = None
        self.capturing = False
        self.frame_counter = 0
        self.temp_dir = "temp_frames"
        # Current step info for overlays
        self.current_step_number = 0
        self.current_step_text = ""

    def start_canvas_interface(self):
        """Initialize the web driver and load the drawing canvas interface"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # Uncomment for headless mode
        # options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.canvas_url)

        # Wait for the canvas to be ready
        self.wait = WebDriverWait(self.driver, 10)

        # The canvas in drawing_canvas.html is created by p5.js and located in #p5-canvas
        self.canvas = self.wait.until(
            EC.presence_of_element_located((By.ID, "p5-canvas"))
        )

        # Wait a bit more for p5.js to fully initialize
        time.sleep(2)

        print("Drawing canvas interface loaded successfully")

    def set_brush(self, brush_type: str, color: str = "default"):
        """Set the brush type and color in the interface using the brush buttons and color pickers"""
        try:
            # Map brush types to button classes in drawing_canvas.html
            brush_button_map = {
                "pen": "pen",
                "marker": "marker",
                "crayon": "crayon",
                "wiggle": "wiggle",
                "spray": "spray",
                "fountain": "fountain"
            }

            if brush_type not in brush_button_map:
                print(f"Error: Invalid brush type '{brush_type}'")
                print(f"Available brush types: {list(brush_button_map.keys())}")
                brush_type = "pen"  # Use default

            # Click the appropriate brush button
            brush_class = brush_button_map[brush_type]
            brush_button = self.driver.find_element(By.CSS_SELECTOR, f".brush-btn.{brush_class}")
            brush_button.click()

            time.sleep(0.2)  # Wait for brush to be set

            # Set color for customizable brushes
            color_customizable_brushes = ["marker", "crayon", "wiggle"]
            if brush_type in color_customizable_brushes and color != "default":
                self.set_brush_color(brush_type, color)

        except Exception as e:
            print(f"Error setting brush '{brush_type}': {e}")
            # Try to set default pen brush
            try:
                pen_button = self.driver.find_element(By.CSS_SELECTOR, ".brush-btn.pen")
                pen_button.click()
                time.sleep(0.2)
            except:
                print("Failed to set default pen brush")

    def set_brush_color(self, brush_type: str, color: str):
        """Set the color for a specific brush type"""
        try:
            # Map brush types to their color picker IDs
            color_picker_map = {
                "marker": "marker-color",
                "crayon": "crayon-color", 
                "wiggle": "wiggle-color"
            }

            if brush_type not in color_picker_map:
                print(f"Warning: Brush '{brush_type}' does not support color customization")
                return

            # Find the color picker element
            color_picker_id = color_picker_map[brush_type]
            color_picker = self.driver.find_element(By.ID, color_picker_id)

            # Set the color value using JavaScript
            self.driver.execute_script(f"document.getElementById('{color_picker_id}').value = '{color}';")

            # Trigger the change event to update the brush color
            self.driver.execute_script(f"document.getElementById('{color_picker_id}').dispatchEvent(new Event('change'));")

            print(f"Set {brush_type} color to {color}")
            time.sleep(0.1)  # Small delay for color to be applied

        except Exception as e:
            print(f"Error setting color for brush '{brush_type}': {e}")

    def set_current_step_info(self, step_number: int, step_text: str):
        """Set the current step information for text overlays"""
        self.current_step_number = step_number
        self.current_step_text = step_text

    def capture_frame_during_drawing(self):
        """Capture a single frame during drawing process with text overlay"""
        if not self.capturing:
            return None
            
        frame_path = os.path.join(self.temp_dir, f"frame_{self.frame_counter:06d}.png")
        
        try:
            # Use JavaScript to capture canvas
            js_code = """
            const canvas = document.querySelector('#p5-canvas canvas');
            return canvas.toDataURL('image/png');
            """
            
            data_url = self.driver.execute_script(js_code)
            
            # Remove the data URL prefix
            image_data = data_url.split(',')[1]
            
            # Decode and save the image
            image_bytes = base64.b64decode(image_data)
            with open(frame_path, 'wb') as f:
                f.write(image_bytes)
            
            # Add text overlay immediately after capture
            if self.current_step_number > 0:
                self._add_text_overlay_to_frame(frame_path, self.current_step_text, self.current_step_number)
                
            self.frame_counter += 1
            return frame_path
            
        except Exception as e:
            print(f"Error capturing frame during drawing: {e}")
            return None

    def _add_text_overlay_to_frame(self, frame_path: str, text: str, step_number: int):
        """Add text overlay to a frame using PIL"""
        try:
            # Load image with PIL
            img = Image.open(frame_path).convert('RGBA')
            
            # Create overlay
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Add semi-transparent background rectangle
            draw.rectangle([(10, 10), (img.width - 10, 100)], fill=(0, 0, 0, 180))
            
            # Try to use a better font, fall back to default if not available
            try:
                title_font = ImageFont.truetype("arial.ttf", 28)
                text_font = ImageFont.truetype("arial.ttf", 18)
            except:
                try:
                    # Try system fonts on different platforms
                    title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)  # macOS
                    text_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
                except:
                    try:
                        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)  # Linux
                        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                    except:
                        # Use default font
                        title_font = ImageFont.load_default()
                        text_font = ImageFont.load_default()
            
            # Add step number
            draw.text((20, 20), f"Step {step_number}", fill=(255, 255, 255, 255), font=title_font)
            
            # Add reasoning text (wrap if too long)
            text_lines = text.split('. ')
            y_offset = 50
            for i, line in enumerate(text_lines[:2]):  # Max 2 lines
                if len(line) > 300:
                    line = line[:297] + "..."
                draw.text((20, y_offset), line, fill=(255, 255, 255, 255), font=text_font)
                y_offset += 25
            
            # Combine images
            img = Image.alpha_composite(img, overlay)
            
            # Convert back to RGB and save
            img = img.convert('RGB')
            img.save(frame_path)
            
        except Exception as e:
            print(f"Error adding text overlay to frame: {e}")

    def start_frame_capture(self, fps=10):
        """Start capturing frames at specified FPS during drawing"""
        self.capturing = True
        capture_interval = 1.0 / fps  # Time between captures
        
        def capture_loop():
            while self.capturing:
                self.capture_frame_during_drawing()
                time.sleep(capture_interval)
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()

    def stop_frame_capture(self):
        """Stop frame capture"""
        self.capturing = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=1.0)

    def execute_stroke_with_capture(self, stroke: dict, capture_fps=30):
        """Execute a single stroke while capturing frames - STAGE 2 LINEAR INTERPOLATION"""
        if not self.canvas:
            print("Warning: Canvas not initialized, skipping stroke")
            return

        # Handle multi-point stroke - coordinates have already been Stage 1 interpolated
        if "x" in stroke and "y" in stroke:
            x_coords = stroke["x"]  # Already Stage 1 interpolated coordinates
            y_coords = stroke["y"]  # Already Stage 1 interpolated coordinates

            if len(x_coords) != len(y_coords) or len(x_coords) < 2:
                print(f"Warning: Invalid stroke, need at least 2 points")
                return

            # Start capturing frames at higher rate for smooth video
            self.start_frame_capture(capture_fps)

            # Execute stroke with STAGE 2 LINEAR INTERPOLATION - same as drawing_canvas_bridge.py
            self._execute_continuous_stroke_stage2(x_coords, y_coords)

            # Stop capturing frames
            self.stop_frame_capture()

    def _execute_continuous_stroke_stage2(self, x_coords: list, y_coords: list):
        """
        STAGE 2: Execute stroke with linear interpolation exactly like drawing_canvas_bridge.py
        Input coordinates are already Stage 1 interpolated (Catmull-Rom splines).
        This adds Stage 2 linear interpolation for smooth browser execution.
        """
        try:
            # Use the EXACT SAME JavaScript code as DrawingCanvasBridge
            js_code = f"""
            // Get the canvas element
            const canvasElement = document.querySelector('#p5-canvas canvas');
            if (!canvasElement) {{
                console.error('Canvas not found');
                return;
            }}

            const rect = canvasElement.getBoundingClientRect();
            const x_coords = {x_coords};
            const y_coords = {y_coords};

            console.log('Starting Stage 2 linear interpolation with Stage 1 interpolated coordinates:', x_coords.length, 'points');

            // Simulate mouse events for drawing
            function simulateMouseEvent(type, x, y) {{
                const event = new MouseEvent(type, {{
                    clientX: x + rect.left,
                    clientY: y + rect.top,
                    bubbles: true,
                    cancelable: true,
                    view: window
                }});
                canvasElement.dispatchEvent(event);
            }}

            // Linear interpolation function (SAME AS drawing_canvas_bridge.py)
            function lerp(start, end, t) {{
                return start + (end - start) * t;
            }}

            // Set initial mouse positions to prevent large first shape
            const startX = x_coords[0];
            const startY = y_coords[0];

            // Set both current and previous mouse positions to the starting point
            if (typeof window.mouseX !== 'undefined') {{
                window.pmouseX = startX;
                window.pmouseY = startY;
                window.mouseX = startX;
                window.mouseY = startY;
                console.log('Set initial mouse positions to:', startX, startY);
            }}

            // Also try setting the global variables that p5.js might use
            if (typeof pmouseX !== 'undefined') {{
                pmouseX = startX;
                pmouseY = startY;
                mouseX = startX;
                mouseY = startY;
            }}

            // Start the drawing sequence
            simulateMouseEvent('mousedown', startX, startY);

            // Small delay after mousedown, then start moving
            setTimeout(() => {{
                console.log('Starting Stage 2 linear interpolation movement');

                // Create smooth interpolated movement between Stage 1 points (EXACT SAME AS drawing_canvas_bridge.py)
                let currentPointIndex = 0;
                const segmentDuration = 50; // 50ms between Stage 1 interpolated points
                const interpolationSteps = 2; // Number of linear interpolation steps per segment
                const stepDuration = segmentDuration / interpolationSteps; // ~25ms per step

                function drawNextSegment() {{
                    if (currentPointIndex >= x_coords.length - 1) {{
                        // End the stroke
                        setTimeout(() => {{
                            simulateMouseEvent('mouseup', x_coords[x_coords.length - 1], y_coords[y_coords.length - 1]);
                            console.log('Stage 2 linear interpolation completed');
                        }}, stepDuration);
                        return;
                    }}

                    const startX = x_coords[currentPointIndex];
                    const startY = y_coords[currentPointIndex];
                    const endX = x_coords[currentPointIndex + 1];
                    const endY = y_coords[currentPointIndex + 1];

                    // Create smooth linear interpolation between current and next Stage 1 point
                    for (let step = 1; step <= interpolationSteps; step++) {{
                        setTimeout(() => {{
                            const t = step / interpolationSteps;
                            const interpX = lerp(startX, endX, t);
                            const interpY = lerp(startY, endY, t);
                            
                            simulateMouseEvent('mousemove', interpX, interpY);
                            
                            // If this is the last step of this segment, move to next segment
                            if (step === interpolationSteps) {{
                                currentPointIndex++;
                                setTimeout(drawNextSegment, stepDuration);
                            }}
                        }}, step * stepDuration);
                    }}
                }}

                // Start drawing the first segment
                drawNextSegment();
            }}, 100);  // 100ms initial delay (same as drawing_canvas_bridge.py)
            """

            self.driver.execute_script(js_code)

            # Wait for the stroke to complete (50ms per Stage 1 point + buffer)
            total_duration = len(x_coords) * 0.05 + 0.5
            time.sleep(total_duration)

        except Exception as e:
            print(f"Warning: Stage 2 stroke execution failed: {e}")

    def _interpolate_stroke_catmull_rom(self, x_coords: list, y_coords: list):
        """
        DEPRECATED: This method is no longer used since Stage 1 interpolation 
        is now done during parsing, exactly like the real drawing system.
        """
        # This is now handled in _validate_and_interpolate_stroke_stage1
        return x_coords, y_coords

    def execute_instruction_with_capture(self, instruction: DrawingInstruction, step_number: int, capture_fps=30):
        """Execute a complete drawing instruction while capturing frames"""
        print(f"Executing instruction: {instruction.reasoning}")
        print(f"Using brush: {instruction.brush}, color: {instruction.color}")

        # Set current step info for text overlays
        self.set_current_step_info(step_number, instruction.reasoning)

        # Set the brush and color
        self.set_brush(instruction.brush, instruction.color)

        # Execute all strokes with frame capture
        for i, stroke in enumerate(instruction.strokes):
            print(f"  Drawing stroke {i+1}/{len(instruction.strokes)}: {stroke['description']}")
            self.execute_stroke_with_capture(stroke, capture_fps)

    def close(self):
        """Close the web driver"""
        self.stop_frame_capture()  # Make sure capture is stopped
        if self.driver:
            self.driver.quit()
            print("Canvas interface closed")

class DrawingVideoGeneratorLite:
    """
    Lightweight video generator that captures frames during the actual drawing process.
    """
    
    def __init__(self, canvas_url: str = None, capture_fps: int = 30):
        """
        Initialize the video generator.
        
        Args:
            canvas_url: URL to the drawing canvas HTML file
            capture_fps: Frames per second to capture during drawing (higher = smoother video)
        """
        self.bridge = DrawingCanvasBridgeVideoCapture(canvas_url)
        self.capture_fps = capture_fps
        self.temp_dir = "temp_frames"
        
    def parse_session_log(self, log_file_path: str):
        """
        Parse the session log file to extract drawing instructions.
        Applies STAGE 1 interpolation - same as free_drawing_agent.py does.
        
        Args:
            log_file_path: Path to the session log file
            
        Returns:
            List of parsed drawing instructions with Stage 1 interpolated coordinates
        """
        instructions = []
        
        with open(log_file_path, 'r') as file:
            content = file.read()
            
        # Split by step sections - updated pattern for drawing agent logs
        step_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] Step\n(.*?)(?=\n\[|\n--------------------------------------------------|\Z)'
        steps = re.findall(step_pattern, content, re.DOTALL)
        
        for timestamp, step_content in steps:
            try:
                # Extract the JSON response - it comes after "Raw Response:" in drawing agent logs
                # Try multiple patterns to handle different log formats
                json_match = None
                
                # Pattern 1: Multi-line JSON with reasoning field (most common)
                json_match = re.search(r'Raw Response:\n(\{.*?\n\})', step_content, re.DOTALL)
                
                # Pattern 2: JSON until next section delimiter
                if not json_match:
                    json_match = re.search(r'Raw Response:\n(\{.*?)(?=\n\n--|\Z)', step_content, re.DOTALL)
                
                # Pattern 3: Single line JSON (fallback)
                if not json_match:
                    json_match = re.search(r'Raw Response:\n(\{[^}]*\})', step_content, re.DOTALL)
                
                if json_match:
                    raw_json_str = json_match.group(1)
                    
                    # More careful JSON cleaning - preserve structure
                    # Remove only unnecessary whitespace and newlines, but keep closing braces
                    json_str = re.sub(r'\n\s+', ' ', raw_json_str)  # Replace newlines+spaces with single space
                    json_str = re.sub(r'\s+', ' ', json_str)         # Multiple spaces to single space
                    json_str = json_str.strip()                      # Remove leading/trailing whitespace
                    
                    try:
                        instruction_data = json.loads(json_str)
                        
                        # Apply STAGE 1 interpolation - same as free_drawing_agent.py _validate_and_sanitize
                        validated_strokes = []
                        for stroke in instruction_data.get('strokes', []):
                            validated_stroke = self._validate_and_interpolate_stroke_stage1(
                                stroke.get('x', []),
                                stroke.get('y', []), 
                                stroke.get('t', []),
                                stroke.get('description', 'stroke')
                            )
                            if validated_stroke:
                                validated_strokes.append(validated_stroke)
                        
                        # Create DrawingInstruction object with Stage 1 interpolated coordinates
                        from dataclasses import dataclass
                        @dataclass
                        class DrawingInstruction:
                            brush: str
                            color: str
                            strokes: list
                            reasoning: str
                        
                        instruction = DrawingInstruction(
                            brush=instruction_data.get('brush', 'pen'),
                            color=instruction_data.get('color', 'default'),
                            strokes=validated_strokes,
                            reasoning=instruction_data.get('reasoning', 'No reasoning provided')
                        )
                        
                        instructions.append({
                            'timestamp': timestamp,
                            'instruction': instruction,
                            'step_number': len(instructions) + 1
                        })
                        
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse JSON for step at {timestamp}: {e}")
                        print(f"JSON content (first 300 chars): {json_str[:300]}")
                        print(f"JSON content (around error position): ...{json_str[max(0, e.pos-50):e.pos+50]}...")
                        print(f"Full JSON content: {repr(json_str)}")
                        
                        # Try to fix common JSON issues
                        try:
                            # Remove trailing commas
                            fixed_json = re.sub(r',(\s*[}\]])', r'\1', json_str)
                            # Fix any double commas
                            fixed_json = re.sub(r',,+', ',', fixed_json)
                            # Try parsing the fixed version
                            instruction_data = json.loads(fixed_json)
                            print(f"Successfully parsed JSON after fixing!")
                            
                            # Apply STAGE 1 interpolation - same as free_drawing_agent.py _validate_and_sanitize
                            validated_strokes = []
                            for stroke in instruction_data.get('strokes', []):
                                validated_stroke = self._validate_and_interpolate_stroke_stage1(
                                    stroke.get('x', []),
                                    stroke.get('y', []), 
                                    stroke.get('t', []),
                                    stroke.get('description', 'stroke')
                                )
                                if validated_stroke:
                                    validated_strokes.append(validated_stroke)
                            
                            # Create DrawingInstruction object with Stage 1 interpolated coordinates
                            from dataclasses import dataclass
                            @dataclass
                            class DrawingInstruction:
                                brush: str
                                color: str
                                strokes: list
                                reasoning: str
                            
                            instruction = DrawingInstruction(
                                brush=instruction_data.get('brush', 'pen'),
                                color=instruction_data.get('color', 'default'),
                                strokes=validated_strokes,
                                reasoning=instruction_data.get('reasoning', 'No reasoning provided')
                            )
                            
                            instructions.append({
                                'timestamp': timestamp,
                                'instruction': instruction,
                                'step_number': len(instructions) + 1
                            })
                            
                        except json.JSONDecodeError as e2:
                            print(f"Failed to parse even after fixing: {e2}")
                            # Skip this step
                            continue
                        
                else:
                    print(f"WARNING: No JSON found for step at {timestamp}")
                    print(f"Step content preview: {step_content[:500]}")
                    print(f"Looking for 'Raw Response:' in content...")
                    if 'Raw Response:' in step_content:
                        raw_response_index = step_content.find('Raw Response:')
                        print(f"Found 'Raw Response:' at position {raw_response_index}")
                        print(f"Content after 'Raw Response:': {step_content[raw_response_index:raw_response_index+300]}")
                    else:
                        print("'Raw Response:' not found in step content")
                
            except Exception as e:
                print(f"Warning: Failed to process step at {timestamp}: {e}")
                
        print(f"Successfully parsed {len(instructions)} drawing instructions with Stage 1 interpolation")
        return instructions

    def _validate_and_interpolate_stroke_stage1(self, x_coords, y_coords, timing, description):
        """
        STAGE 1: Apply the same validation and interpolation logic as free_drawing_agent.py
        This exactly replicates _validate_and_sanitize() -> _interpolate_stroke_with_timing()
        """
        # Convert to lists if needed
        if not isinstance(x_coords, list):
            x_coords = [x_coords]
        if not isinstance(y_coords, list):
            y_coords = [y_coords]
        if not isinstance(timing, list):
            timing = []
        
        # Ensure same length for x and y
        min_len = min(len(x_coords), len(y_coords))
        x_coords = x_coords[:min_len]
        y_coords = y_coords[:min_len]
        
        # Validate timing array - should have length = len(x_coords) - 1
        expected_timing_len = max(0, len(x_coords) - 1)
        if len(timing) != expected_timing_len:
            timing = [2] * expected_timing_len  # Default medium speed
        
        # Clamp timing values to 1-5
        timing = [max(1, min(5, int(t))) for t in timing]
        
        # Clamp coordinates to canvas bounds
        x_coords = [max(0, min(850, x)) for x in x_coords]
        y_coords = [max(0, min(500, y)) for y in y_coords]
        
        # Ensure at least 2 points for a stroke
        if len(x_coords) < 2:
            return None
        
        # Apply Catmull-Rom spline interpolation with timing (EXACT SAME AS free_drawing_agent.py)
        interpolated_x, interpolated_y = self._interpolate_stroke_with_timing_stage1(
            x_coords, y_coords, timing
        )
        
        return {
            'x': interpolated_x,        # Stage 1 interpolated coordinates
            'y': interpolated_y,        # Stage 1 interpolated coordinates
            'original_x': x_coords,     # Original coordinates from LLM
            'original_y': y_coords,     # Original coordinates from LLM
            'timing': timing,           # Timing values used for interpolation
            'description': description
        }

    def _interpolate_stroke_with_timing_stage1(self, x_coords, y_coords, timing):
        """
        STAGE 1: EXACT COPY of _interpolate_stroke_with_timing from free_drawing_agent.py
        Interpolate stroke points using Catmull-Rom splines with timing-based steps.
        """
        if len(x_coords) != len(y_coords):
            return x_coords, y_coords

        if len(timing) != len(x_coords) - 1:
            # If timing doesn't match, use default timing of 2 for all segments
            timing = [2] * (len(x_coords) - 1)

        # For smooth curves, we need at least 2 points
        if len(x_coords) < 2:
            return x_coords, y_coords

        interpolated_x = []
        interpolated_y = []

        # Helper function for Catmull-Rom spline interpolation
        def catmull_rom_point(p0, p1, p2, p3, t):
            """Calculate point on Catmull-Rom spline"""
            t2 = t * t
            t3 = t2 * t

            return 0.5 * ((2 * p1) +
                         (-p0 + p2) * t +
                         (2*p0 - 5*p1 + 4*p2 - p3) * t2 +
                         (-p0 + 3*p1 - 3*p2 + p3) * t3)

        # For each segment, create smooth curve interpolation
        for i in range(len(x_coords) - 1):
            # Get control points for Catmull-Rom spline
            # We need 4 points: p0, p1 (current segment start), p2 (current segment end), p3

            # Handle edge cases for first and last segments
            if i == 0:
                # First segment: extrapolate p0
                p0_x = x_coords[0] - (x_coords[1] - x_coords[0])
                p0_y = y_coords[0] - (y_coords[1] - y_coords[0])
            else:
                p0_x = x_coords[i - 1]
                p0_y = y_coords[i - 1]

            p1_x, p1_y = x_coords[i], y_coords[i]
            p2_x, p2_y = x_coords[i + 1], y_coords[i + 1]

            if i == len(x_coords) - 2:
                # Last segment: extrapolate p3
                p3_x = x_coords[-1] + (x_coords[-1] - x_coords[-2])
                p3_y = y_coords[-1] + (y_coords[-1] - y_coords[-2])
            else:
                p3_x = x_coords[i + 2]
                p3_y = y_coords[i + 2]

            # Number of interpolation steps based on timing (EXACT SAME AS free_drawing_agent.py)
            steps = max(2, min(8, timing[i] * 2))  # More steps for smoother curves

            # Generate curve points
            for step in range(steps):
                t = step / (steps - 1)  # 0 to 1

                curve_x = catmull_rom_point(p0_x, p1_x, p2_x, p3_x, t)
                curve_y = catmull_rom_point(p0_y, p1_y, p2_y, p3_y, t)

                interpolated_x.append(curve_x)
                interpolated_y.append(curve_y)

        # Remove duplicate points (the last point of each segment = first point of next)
        if len(interpolated_x) > 1:
            final_x = [interpolated_x[0]]
            final_y = [interpolated_y[0]]

            for i in range(1, len(interpolated_x)):
                # Only add point if it's sufficiently different from the last one
                if abs(interpolated_x[i] - final_x[-1]) > 1 or abs(interpolated_y[i] - final_y[-1]) > 1:
                    final_x.append(interpolated_x[i])
                    final_y.append(interpolated_y[i])

            return final_x, final_y

        return interpolated_x, interpolated_y

    def setup_temp_directory(self):
        """Create temporary directory for frame storage."""
        # Set temp directory on bridge too
        self.bridge.temp_dir = self.temp_dir
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        else:
            # Clean existing frames
            for file in os.listdir(self.temp_dir):
                if file.endswith('.png'):
                    os.remove(os.path.join(self.temp_dir, file))

    def generate_video(self, log_file_path: str, output_path: str = None):
        """
        Generate video from session log by capturing frames during drawing.
        Automatically calculates FPS to match actual drawing duration.
        
        Args:
            log_file_path: Path to the session log file
            output_path: Output video file path (optional)
            
        Returns:
            Path to the generated video file
        """
        # Parse instructions from log
        instruction_steps = self.parse_session_log(log_file_path)
        
        if not instruction_steps:
            print("Error: No drawing instructions found in log file")
            return None
        
        # Calculate actual drawing duration to determine proper FPS
        actual_drawing_duration = self._calculate_actual_drawing_duration(instruction_steps)
        
        # Setup output paths
        if output_path is None:
            # Extract session info from log filename
            log_filename = os.path.basename(log_file_path)
            session_id = log_filename.replace('session_responses_', '').replace('.txt', '')
            output_dir = "output/video"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"drawing_session_{session_id}.mp4")
        
        print(f"🎬 Generating video with Catmull-Rom stroke interpolation...")
        print(f"📁 Output: {output_path}")
        print(f"⏱️  Expected drawing duration: {actual_drawing_duration:.1f} seconds")
        print(f"🎥 Video will use dynamic FPS to match actual drawing time")
        
        # Setup temporary directory
        self.setup_temp_directory()
        
        # Start canvas interface
        print("🌐 Starting canvas interface...")
        self.bridge.start_canvas_interface()
        
        try:
            # Capture initial blank canvas frame with initial text
            self.bridge.set_current_step_info(0, "Starting drawing session...")
            initial_frame = self.bridge.capture_frame_during_drawing()
            
            # Execute each instruction with frame capture using TWO-STAGE INTERPOLATION
            total_stroke_count = sum(len(instruction.strokes) for step_data in instruction_steps for instruction in [step_data['instruction']])
            print(f"🖌️  Total strokes to execute: {total_stroke_count}")
            print(f"📝 Using TWO-STAGE INTERPOLATION (exactly matching drawing agent):")
            print(f"    Stage 1: Catmull-Rom spline interpolation with timing (applied during parsing)")
            print(f"    Stage 2: Linear interpolation (50ms/segment, 2 steps) during execution")
            
            for i, step_data in enumerate(instruction_steps):
                instruction = step_data['instruction']
                step_num = i + 1
                
                print(f"\n🎨 Step {step_num}/{len(instruction_steps)}: {instruction.brush}")
                print(f"   {instruction.reasoning}")
                
                # Show interpolation info for each stroke
                for j, stroke in enumerate(instruction.strokes):
                    original_points = len(stroke.get('original_x', []))
                    stage1_points = len(stroke.get('x', []))
                    print(f"     Stroke {j+1}: {original_points} original → {stage1_points} Stage 1 interpolated points")
                
                # Execute the drawing instruction with real-time capture and text overlays
                self.bridge.execute_instruction_with_capture(instruction, step_num, self.capture_fps)
                
                # Brief pause between steps
                time.sleep(0.5)
            
            # Calculate optimal FPS for video to match actual drawing duration
            optimal_fps = self._calculate_optimal_fps(actual_drawing_duration)
            
            # Generate video from frames with calculated FPS
            print(f"🎞️ Compiling frames into video at {optimal_fps:.1f} fps...")
            self._create_video_from_frames_imageio(output_path, optimal_fps)
            
            print(f"✅ Video generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            # Cleanup
            self.bridge.close()
            self._cleanup_temp_files()
    
    def _calculate_actual_drawing_duration(self, instruction_steps):
        """
        Calculate the actual duration it would take to draw these instructions
        based on the real drawing system timing. Uses Stage 1 interpolated coordinates.
        """
        total_duration = 0.0
        
        for step_data in instruction_steps:
            instruction = step_data['instruction']
            
            # Time for each stroke based on Stage 1 interpolated coordinates
            # (Same timing as real system: 50ms per Stage 1 interpolated point)
            for stroke in instruction.strokes:
                if "x" in stroke and "y" in stroke:
                    stage1_coords = stroke["x"]  # Stage 1 interpolated coordinates
                    
                    if len(stage1_coords) >= 2:
                        # Real system: 50ms per Stage 1 interpolated point + delays
                        stroke_duration = len(stage1_coords) * 0.05 + 0.1 + 0.5
                        total_duration += stroke_duration
            
            # Add pause between steps (realistic thinking time)
            total_duration += 1.0  # 1 second between drawing steps
        
        return total_duration
    
    def _calculate_optimal_fps(self, target_duration):
        """
        Calculate the optimal FPS to make video match the target duration.
        """
        # Count total frames captured
        frame_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.png')]
        total_frames = len(frame_files)
        
        if total_frames == 0 or target_duration <= 0:
            return self.capture_fps  # Fallback to original FPS
        
        # Calculate FPS needed to achieve target duration
        optimal_fps = total_frames / target_duration
        
        # Clamp FPS to reasonable range (5-30 fps)
        optimal_fps = max(5, min(30, optimal_fps))
        
        print(f"📊 Frame analysis: {total_frames} frames captured")
        print(f"🎯 Target duration: {target_duration:.1f} seconds")
        print(f"📈 Calculated optimal FPS: {optimal_fps:.1f}")
        
        return optimal_fps
    
    def _create_video_from_frames_imageio(self, output_path: str, fps: float = None):
        """
        Create MP4 video from captured frames using imageio with specified FPS.
        
        Args:
            output_path: Path for the output video file
            fps: Frames per second for the video (uses capture_fps if None)
        """
        if fps is None:
            fps = self.capture_fps
            
        # Get all frame files
        frame_files = sorted([f for f in os.listdir(self.temp_dir) if f.endswith('.png')])
        
        if not frame_files:
            raise Exception("No frames found to create video")
        
        print(f"Creating video from {len(frame_files)} captured frames at {fps:.1f} fps...")
        
        # Create video writer with the calculated FPS
        writer = imageio.get_writer(output_path, fps=fps, codec='libx264', 
                                   quality=8, macro_block_size=None)
        
        try:
            for i, frame_file in enumerate(frame_files):
                frame_path = os.path.join(self.temp_dir, frame_file)
                
                # Load frame as numpy array
                frame = imageio.imread(frame_path)
                
                # Add frame to video
                writer.append_data(frame)
                
                # Progress indicator
                if (i + 1) % 50 == 0:
                    print(f"  Processed {i + 1}/{len(frame_files)} frames...")
        
        finally:
            writer.close()
        
        # Calculate and display final video duration
        video_duration = len(frame_files) / fps
        print(f"🎬 Final video duration: {video_duration:.1f} seconds at {fps:.1f} fps")
    
    def _cleanup_temp_files(self):
        """Clean up temporary frame files."""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")

def main():
    """Main function to generate video from session log."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate MP4 video showing real-time drawing process with text overlays (Lite version)')
    parser.add_argument('log_file', help='Path to the session log file')
    parser.add_argument('--output', '-o', help='Output video file path (optional)')
    parser.add_argument('--fps', type=int, default=30, help='Capture FPS during drawing (default: 30)')
    
    args = parser.parse_args()
    
    # Check if log file exists
    if not os.path.exists(args.log_file):
        print(f"Error: Log file not found: {args.log_file}")
        return
    
    # Create video generator
    generator = DrawingVideoGeneratorLite(capture_fps=args.fps)
    
    # Generate video
    output_path = generator.generate_video(args.log_file, args.output)
    
    if output_path:
        print(f"\n🎉 Real-time drawing video with text overlays generated!")
        print(f"📁 Video saved to: {output_path}")
        
        # Get file size
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"📊 File size: {file_size:.1f} MB")
        print(f"🎬 Video shows strokes being drawn in real-time at {args.fps} fps")
        print(f"📝 All frames include step numbers and reasoning text overlays")
    else:
        print("\n❌ Video generation failed!")

if __name__ == "__main__":
    # If run without arguments, try to find the most recent log file
    import sys
    if len(sys.argv) == 1:
        log_dir = "output/log"
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.txt')]
            if log_files:
                # Use most recent log file that has a session_responses_ prefix
                log_files = [f for f in log_files if f.startswith('session_responses_')]
                latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
                log_path = os.path.join(log_dir, latest_log)
                print(f"🔍 Using most recent log file: {log_path}")
                
                generator = DrawingVideoGeneratorLite(capture_fps=30)
                output_path = generator.generate_video(log_path)
                
                if output_path:
                    print(f"\n🎉 Real-time drawing video with text overlays generated!")
                    print(f"📁 Video saved to: {output_path}")
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"📊 File size: {file_size:.1f} MB")
                sys.exit(0)
        
        print("No log files found. Please provide a log file path as argument.")
        print("Usage: python generate_drawing_video_lite.py <log_file_path>")
    else:
        main() 