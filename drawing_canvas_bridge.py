#!/usr/bin/env python3
"""
Bridge for drawing_canvas.html
This module provides integration between the FreeDrawingAgent and the drawing_canvas.html interface.
"""

import time
import threading
import imageio
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from free_drawing_agent import FreeDrawingAgent, DrawingInstruction
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DrawingCanvasBridge:
    """
    Bridge between the FreeDrawingAgent and the drawing_canvas.html interface.
    Handles the execution of drawing instructions on the HTML canvas.
    Now includes real-time video capture capabilities during the drawing process.
    """

    def __init__(self, canvas_url: str = None, enable_video_capture: bool = False, capture_fps: int = 30):
        self.canvas_url = canvas_url or f"file://{os.path.abspath('drawing_canvas.html')}"
        self.driver = None
        self.canvas = None
        self.wait = None

        # Video capture settings
        self.enable_video_capture = enable_video_capture
        self.capture_fps = capture_fps
        self.capturing = False
        self.frame_counter = 0
        self.temp_dir = "temp_frames"
        self.video_writer = None
        self.capture_thread = None
        # Current step info for overlays
        self.current_step_number = 0
        self.current_step_text = ""
        self.session_start_time = None

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

        # Initialize video capture if enabled
        if self.enable_video_capture:
            self._initialize_video_capture()

    def _initialize_video_capture(self):
        """Initialize video capture system"""
        self.session_start_time = datetime.now()

        # Create temp directory for frames
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        else:
            # Clean existing frames
            for file in os.listdir(self.temp_dir):
                if file.endswith('.png'):
                    os.remove(os.path.join(self.temp_dir, file))

        print(f"🎥 Video capture initialized at {self.capture_fps} fps")

    def start_video_capture(self, output_path: str = None):
        """Start capturing video frames during drawing"""
        if not self.enable_video_capture:
            return

        if output_path is None:
            timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
            output_path = f"output/video/drawing_session_{timestamp}.mp4"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        self.video_output_path = output_path
        self.capturing = True
        self.frame_counter = 0

        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

        print(f"🎬 Started video capture: {output_path}")

    def stop_video_capture(self):
        """Stop video capture and compile video"""
        if not self.enable_video_capture or not self.capturing:
            return

        self.capturing = False

        # Wait for capture thread to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        # Compile video from frames
        self._compile_video()

        # Cleanup temp frames
        self._cleanup_temp_frames()

        print(f"🎉 Video capture completed: {self.video_output_path}")

    def _capture_loop(self):
        """Continuous frame capture loop"""
        capture_interval = 1.0 / self.capture_fps

        while self.capturing:
            try:
                self._capture_frame()
                time.sleep(capture_interval)
            except Exception as e:
                print(f"Frame capture error: {e}")

    def _capture_frame(self):
        """Capture a single frame with text overlay"""
        if not self.capturing or not self.driver:
            return

        try:
            # Use JavaScript to capture canvas
            js_code = """
            const canvas = document.querySelector('#p5-canvas canvas');
            return canvas.toDataURL('image/png');
            """

            data_url = self.driver.execute_script(js_code)

            # Remove the data URL prefix
            image_data = data_url.split(',')[1]

            # Decode the image
            image_bytes = base64.b64decode(image_data)

            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            # Add text overlay if step info is available
            if self.current_step_number > 0:
                image = self._add_text_overlay(image)

            # Save frame
            frame_path = os.path.join(self.temp_dir, f"frame_{self.frame_counter:06d}.png")
            image.save(frame_path)

            self.frame_counter += 1

        except Exception as e:
            print(f"Error capturing frame: {e}")

    def _add_text_overlay(self, image: Image.Image) -> Image.Image:
        """Add text overlay to frame"""
        try:
            # Create overlay
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Add semi-transparent background rectangle
            draw.rectangle([(10, 10), (image.width - 10, 100)], fill=(0, 0, 0, 180))

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
            draw.text((20, 20), f"Step {self.current_step_number}", fill=(255, 255, 255, 255), font=title_font)

            # Add reasoning text (wrap if too long)
            if self.current_step_text:
                text_lines = self.current_step_text.split('. ')
                y_offset = 50
                for i, line in enumerate(text_lines[:2]):  # Max 2 lines
                    if len(line) > 80:
                        line = line[:77] + "..."
                    draw.text((20, y_offset), line, fill=(255, 255, 255, 255), font=text_font)
                    y_offset += 25

            # Combine images
            image = Image.alpha_composite(image.convert('RGBA'), overlay)
            return image.convert('RGB')

        except Exception as e:
            print(f"Error adding text overlay: {e}")
            return image

    def _compile_video(self):
        """Compile frames into MP4 video"""
        try:
            # Get all frame files
            frame_files = sorted([f for f in os.listdir(self.temp_dir) if f.endswith('.png')])

            if not frame_files:
                print("No frames to compile into video")
                return

            print(f"🎞️ Compiling {len(frame_files)} frames into video...")

            # Use lower FPS for video playback to make it longer
            # We capture at 30 fps but play back at 10 fps = 3x longer video
            playback_fps = 10

            # Create video writer with lower playback FPS
            writer = imageio.get_writer(self.video_output_path, fps=playback_fps,
                                     codec='libx264', quality=8)

            try:
                for i, frame_file in enumerate(frame_files):
                    frame_path = os.path.join(self.temp_dir, frame_file)
                    frame = imageio.imread(frame_path)
                    writer.append_data(frame)

                    # Progress indicator
                    if (i + 1) % 100 == 0:
                        print(f"  Processed {i + 1}/{len(frame_files)} frames...")

            finally:
                writer.close()

            # Calculate video duration with playback FPS
            video_duration = len(frame_files) / playback_fps
            capture_duration = len(frame_files) / self.capture_fps
            print(f"📹 Video duration: {video_duration:.1f} seconds (captured in {capture_duration:.1f}s real-time)")
            print(f"🎬 Playback: {playback_fps} fps (captured at {self.capture_fps} fps)")

        except Exception as e:
            print(f"Error compiling video: {e}")

    def _cleanup_temp_frames(self):
        """Clean up temporary frame files"""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")

    def set_current_step_info(self, step_number: int, step_text: str):
        """Set current step information for video overlays"""
        self.current_step_number = step_number
        self.current_step_text = step_text

    def set_brush(self, brush_type: str, color: str = "default"):
        """Set the brush type and color in the interface using the brush buttons and color pickers"""
        print(f"Setting brush: {brush_type} with color: {color}")
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

            time.sleep(0.5)  # Wait for brush to be set

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
                time.sleep(0.5)
            except:
                print("Failed to set default pen brush")

    def set_brush_color(self, brush_type: str, color: str):
        """Set the color using the new color button system"""
        try:
            color_found = False
            
            # The dropdowns are hidden by default, so we need to open them to search for colors
            # Get all main color swatches (color1, color2, color3)
            main_swatches = self.driver.find_elements(By.CSS_SELECTOR, ".main-color-swatch")
            
            for swatch in main_swatches:
                # Open this dropdown by clicking the main swatch
                swatch.click()
                time.sleep(0.3)  # Wait for dropdown to appear
                
                # Now search for the color in the opened dropdown
                try:
                    # Get all palette colors in the currently open dropdown
                    visible_palette_colors = self.driver.find_elements(By.CSS_SELECTOR, ".dropdown-content.show .palette-color")
                    
                    for palette_color in visible_palette_colors:
                        palette_bg_color = self.driver.execute_script(
                            "return arguments[0].style.backgroundColor;", palette_color
                        )
                        
                        # Convert and compare colors
                        if self._colors_match(palette_bg_color, color):
                            palette_color.click()
                            color_found = True
                            print(f"Selected existing palette color {color} for {brush_type}")
                            break
                    
                    if color_found:
                        break
                        
                    # Close this dropdown by clicking outside or on the swatch again
                    self.driver.execute_script("document.querySelectorAll('.dropdown-content').forEach(dd => dd.classList.remove('show')); activeDropdown = null;")
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"Error searching in dropdown: {e}")
                    continue
            
            # If color not found in any palette, set it as a custom color
            if not color_found:
                # Use the selectColor function to set a custom color on color1
                self.driver.execute_script(f"selectColor('{color}', 'color1');")
                print(f"Set custom color {color} on main color swatch for {brush_type}")
            
            time.sleep(0.2)  # Small delay for color to be applied

        except Exception as e:
            print(f"Error setting color for brush '{brush_type}': {e}")
    
    def _colors_match(self, color1: str, color2: str) -> bool:
        """Helper method to compare colors in different formats"""
        try:
            # Convert both colors to hex format for comparison
            def to_hex(color):
                if color.startswith('#'):
                    return color.upper()
                elif color.startswith('rgb'):
                    # Extract RGB values from rgb(r, g, b) format
                    import re
                    rgb_values = re.findall(r'\d+', color)
                    if len(rgb_values) >= 3:
                        r, g, b = int(rgb_values[0]), int(rgb_values[1]), int(rgb_values[2])
                        return f"#{r:02X}{g:02X}{b:02X}"
                return color.upper()
            
            return to_hex(color1) == to_hex(color2)
        except:
            return False

    def execute_stroke(self, stroke: dict,brush_type: str = "pen"):
        """Execute a single stroke on the canvas"""
        if not self.canvas:
            print("Warning: Canvas not initialized, skipping stroke")
            return

        # Handle multi-point stroke
        best_params = {"fountain": [28,70], "marker": [8,20], "spray": [20,50], "wiggle": [8,20], "crayon": [8,20]}
        step_length = best_params[brush_type][0]
        step_duration = best_params[brush_type][1]
        if "x" in stroke and "y" in stroke:
            x_coords = stroke["x"]
            y_coords = stroke["y"]

            # Execute as a continuous stroke using JavaScript
            self._execute_continuous_stroke(x_coords = x_coords, y_coords = y_coords, step_length = step_length, step_duration = step_duration, brush_type = brush_type)

    def _execute_continuous_stroke(self, x_coords: list, y_coords: list, step_length: int = 20, step_duration: int = 50,brush_type: str = "fountain"):
        """Execute a continuous stroke using JavaScript mouse events with smooth interpolation"""
        print(f"Executing continuous stroke with step_length: {step_length} and step_duration: {step_duration}")
        # Calculate total time for stroke execution
        total_time = 0
        for i in range(len(x_coords)-1):
            # Calculate distance between points
            distance = ((x_coords[i+1] - x_coords[i])**2 + (y_coords[i+1] - y_coords[i])**2)**0.5
            # Calculate steps needed for this segment
            steps_per_segment = max(1, int(distance / step_length))
            # Add time for each step in segment
            total_time += steps_per_segment * step_duration
        print(f"Total stroke execution time: {total_time/1000:.2f} seconds")
        js_code = f'''
        const x_coords = {x_coords};
        const y_coords = {y_coords};
        const fixed_step_length = {step_length};
        const step_delay = {step_duration}; // delay between each point

        function lerp(a, b, t) {{ return a + (b - a) * t; }}

        async function drawStroke() {{
            for (let i = 0; i < x_coords.length - 1; i++) {{
                const startX = x_coords[i];
                const startY = y_coords[i];
                const endX = x_coords[i+1];
                const endY = y_coords[i+1];

                // Calculate distance between this pair of points
                const distance = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));

                // Calculate steps needed for this specific stroke
                const steps_per_segment = Math.max(1, Math.floor(distance / fixed_step_length));

                for (let s = 0; s <= steps_per_segment; s++) {{
                    const t = s / steps_per_segment;
                    const interpX = lerp(startX, endX, t);
                    const interpY = lerp(startY, endY, t);
                    window.pmouseX = (s === 0) ? startX : window.mouseX;
                    window.pmouseY = (s === 0) ? startY : window.mouseY;
                    window.mouseX = interpX;
                    window.mouseY = interpY;

                    // Only call brush_type if there is movement
                    if ((window.mouseX !== window.pmouseX) || (window.mouseY !== window.pmouseY)) {{
                        if (typeof window['{brush_type}'] === 'function') {{
                            window['{brush_type}']();
                        }}
                    }}

                    // Add delay between each point for smooth drawing
                    if (step_delay > 0 && s < steps_per_segment) {{
                        await new Promise(resolve => setTimeout(resolve, step_delay));
                    }}
                }}
            }}
        }}

        drawStroke();
        '''
        self.driver.execute_script(js_code)
        #wait for the stroke to finish
        time.sleep(total_time/1000 + 0.5)


    def execute_instruction(self, instruction: DrawingInstruction, step_number: int = 0):
        """Execute a complete drawing instruction with optional video capture"""
        print(f"Executing instruction: {instruction}")
        # print(f"Executing instruction: {instruction.thinking}")
        print(f"Using brush: {instruction.brush}, color: {instruction.color}")

        # Set current step info for video overlays
        if self.enable_video_capture:
            self.set_current_step_info(step_number, instruction.thinking)

        # Set the brush and color
        self.set_brush(instruction.brush, instruction.color)

        # Execute all strokes
        for i, stroke in enumerate(instruction.strokes):
            print(f"  Drawing stroke {i+1}/{len(instruction.strokes)}")
            self.execute_stroke(stroke,instruction.brush)

    def capture_canvas(self, filename: str = "current_canvas.png"):
        """Capture the current canvas as an image"""
        try:
            # Use p5.js save function to capture the canvas
            js_code = """
            // Get the p5 canvas and convert to data URL
            const canvas = document.querySelector('#p5-canvas canvas');
            return canvas.toDataURL('image/png');
            """

            data_url = self.driver.execute_script(js_code)

            # Remove the data URL prefix
            image_data = data_url.split(',')[1]

            # Decode and save the image
            image_bytes = base64.b64decode(image_data)
            with open(filename, 'wb') as f:
                f.write(image_bytes)

            print(f"Canvas captured and saved as '{filename}'")
            return filename

        except Exception as e:
            print(f"Error capturing canvas: {e}")
            return None

    def clear_canvas(self):
        """Clear the canvas using the clear button"""
        try:
            clear_button = self.driver.find_element(By.CSS_SELECTOR, ".clear-btn")
            clear_button.click()
            time.sleep(0.5)
            print("Canvas cleared")
        except Exception as e:
            print(f"Error clearing canvas: {e}")

    def close(self):
        """Close the web driver and stop video capture if active"""
        # Stop video capture if it's running
        if self.enable_video_capture and self.capturing:
            self.stop_video_capture()

        if self.driver:
            self.driver.quit()
            print("Canvas interface closed")

class AutomatedDrawingCanvas:
    """
    High-level interface that combines the FreeDrawingAgent with the DrawingCanvasBridge
    for automated creative drawing sessions.
    """

    def __init__(self, api_key: str, canvas_url: str = None, enable_video_capture: bool = False, capture_fps: int = 30,model_type: str = "claude",verbose: bool = False):
        self.agent = FreeDrawingAgent(api_key=api_key,model_type=model_type,verbose=verbose)
        self.bridge = DrawingCanvasBridge(canvas_url=canvas_url, enable_video_capture=enable_video_capture, capture_fps=capture_fps)
        self.enable_video_capture = enable_video_capture

    def start(self):
        """Start the drawing canvas interface"""
        self.bridge.start_canvas_interface()

    def draw_from_canvas(self, canvas_filename: str = "current_canvas.png",
                        question: str = "What would you like to draw next?", step_number: int = 0):
        """
        Analyze the current canvas and execute a drawing instruction.

        Args:
            canvas_filename: Filename to save/load the current canvas
            question: Question to ask the agent about what to draw
            step_number: Step number for video overlays

        Returns:
            The executed DrawingInstruction
        """
        # Capture current canvas state
        self.bridge.capture_canvas(canvas_filename)

        # Get drawing instruction from agent
        instruction = self.agent.create_drawing_instruction(canvas_filename, question)
        # Execute the instruction
        self.bridge.execute_instruction(instruction, step_number)

        return instruction

    def draw_from_emotion(self, canvas_filename: str = "current_canvas.png",
                         emotion: str = None, step_number: int = 0):
        """
        Create a mood-based drawing instruction and execute it.

        Args:
            canvas_filename: Filename to save the current canvas image
            emotion: Optional emotion to express (if None, LLM chooses autonomously)
            step_number: Step number for video overlays

        Returns:
            DrawingInstruction object that was executed
        """
        # Capture current canvas state
        self.bridge.capture_canvas(canvas_filename)

        # Create a random mood first
        if emotion is None:
            random_emotion = self.agent._get_random_mood()
            print(f"Random emotion: {random_emotion}")
            emotion = random_emotion
        instruction = self.agent.create_emotion_drawing_instruction(
            canvas_image_path=canvas_filename, emotion=emotion
        )

        # Execute the instruction
        self.bridge.execute_instruction(instruction, step_number)

        return instruction

    def draw_from_abstract(self, canvas_filename: str = "current_canvas.png", step_number: int = 0):
        """
        Create an abstract, non-representational drawing instruction and execute it.

        Args:
            canvas_filename: Filename to save the current canvas image
            step_number: Step number for video overlays

        Returns:
            DrawingInstruction object that was executed
        """
        # Capture current canvas state
        self.bridge.capture_canvas(canvas_filename)

        # Create abstract drawing instruction
        instruction = self.agent.create_abstract_drawing_instruction(
            canvas_filename
        )

        # Execute the instruction
        self.bridge.execute_instruction(instruction, step_number)

        return instruction

    def creative_session(self, num_iterations: int = 5, output_dir: str = 'output'):
        """
        Run a creative drawing session with multiple iterations.

        Args:
            num_iterations: Number of drawing iterations to perform
            output_dir: Directory to save outputs
        """
        print(f"🎨 Starting creative drawing session with {num_iterations} iterations")

        if self.enable_video_capture:
            print(f"🎥 Video capture enabled - recording drawing process")

        # Create output directory
        os.makedirs(f"{output_dir}", exist_ok=True)

        # Start video capture if enabled
        if self.enable_video_capture:
            video_output = f"{output_dir}/creative_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            self.bridge.start_video_capture(video_output)

        # Capture initial blank canvas
        self.bridge.capture_canvas(f"{output_dir}/canvas_step_0.png")

        instructions = []

        try:
            for i in range(num_iterations):
                print(f"\n--- Iteration {i+1}/{num_iterations} ---")

                canvas_file = f"{output_dir}/canvas_step_{i}.png"

                # Questions to vary the creative process
                # questions = [
                #     "What would you like to draw next?",
                #     "How can you enhance this artwork?",
                #     "What creative element would complement this scene?",
                #     "What interesting detail could you add?",
                #     "How would you continue this artistic expression?"
                # ]

                # question = questions[i % len(questions)]
                question = "What would you like to draw next?"
                instruction = self.draw_from_canvas(canvas_file, question, step_number=i+1)
                instructions.append(instruction)

                # Capture the result
                self.bridge.capture_canvas(f"{output_dir}/canvas_step_{i+1}.png")

                print(f"Agent's thinking: {instruction.thinking}")

            # Save final artwork
            final_canvas = f"{output_dir}/final_artwork.png"
            self.bridge.capture_canvas(final_canvas)

            print(f"\n🎉 Creative session completed!")
            print(f"Final artwork saved as: {final_canvas}")

            if self.enable_video_capture:
                print(f"🎬 Video saved as: {video_output}")

            print(f"\n📋 Session Summary:")
            for i, instruction in enumerate(instructions):
                print(f"  Step {i+1}: {instruction.thinking}")

        finally:
            # Stop video capture if it was started
            if self.enable_video_capture:
                self.bridge.stop_video_capture()

        return instructions

    def close(self):
        """Close the drawing canvas interface"""
        # Finalize agent session logs
        self.agent.close_session_logs()
        self.bridge.close()

def main():
    """Example usage of the AutomatedDrawingCanvas"""
    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return

    # Create the automated drawing canvas
    canvas = AutomatedDrawingCanvas(api_key=api_key)

    try:
        # Start the interface
        canvas.start()

        # Run a creative session
        canvas.creative_session(num_iterations=3)

    except KeyboardInterrupt:
        print("\n⚠️ Session interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during session: {e}")
        import traceback
        traceback.print_exc()

    finally:
        canvas.close()

if __name__ == "__main__":
    main()
